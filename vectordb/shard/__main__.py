import time
import click
import faiss
import numpy as np
import json_tricks as json
import redis.client
from vectordb.utils.rw_lock import rwLock
from threading import Thread, Lock
import redis
from concurrent.futures import ThreadPoolExecutor, Future
import logging
import os
from vectordb.utils.config_parser import parse_config
import socket
import subprocess
import re


logging.basicConfig(level=logging.DEBUG, format='%(threadName)s: %(message)s')

# LOGGER = logging.getLogger(__name__)
class DBShard:
    TIMEOUT_INTERVAL = 5
    
    
    def __init__(self):
        """
        """
        
        # dimension: int, other_shard_ids: list[int] = []
        
        self.cluster_id, self.shard_id, self.dimension = self._get_ids()

        
        index = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIDMap2(index)
        self.lock = rwLock()
        
        redis_host = os.getenv("REDIS_HOST", 'localhost')
        redis_port = os.getenv("REDIS_PORT", 6379)
        redis_db = os.getenv("REDIS_DB", 0)
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.leader_lock = Lock()


        self.HEARTBEAT_KEY = f'Cluster{self.cluster_id}Shard{self.shard_id}Heartbeat'
        self.LEADER_HEARTBEAT_KEY = f'Cluster{self.cluster_id}LeaderHeartbeat'
        self.redis_client.set(self.HEARTBEAT_KEY, self.shard_id, ex=DBShard.TIMEOUT_INTERVAL)


        self.primary_id = None
        # Attempt to become leader as soon as shard is created
        with self.leader_lock:
            self.is_primary = False
            self.failover()


        # list of replicas in the shard
        # self.replicas = [Replica(i, i == primary_id) for i in other_shard_ids if i != shard_id]
        

        self.executor = ThreadPoolExecutor(max_workers=10)
        
        self.shutdown = False
        
        self.heartbeat_thread = Thread(target=self.send_heartbeat, daemon=True).start()
        
        self.monitor_leader_thread = Thread(target=self.monitor_leader_heartbeat, daemon=True).start()
        self.listen_thread = Thread(target = self.process_coord_stream).start()

        
        print("HIII")

    def _get_replica_id(self):

        
        # ! Assumes hostname is in the format: "shard_{replica_id}-d"
        # hostname_str = hostname.split('-')[-1]
        # hostname_str = hostname_str.split('-')[0]
        # return int(hostname_str)
        
        # run this command
        # cat /run/.containerenv | sed -n '2 p' | awk -F '"' 'NF>2{print $2}'
        # result = subprocess.run(
        #     'cat /run/.containerenv | sed -n "2 p" | awk -F \'"\' \'NF>2{print $2}\'',
        #     shell=True,
        #     check=True,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE
        # )
        # shard_name = result.stdout.decode('utf-8').strip()
        
        # print(hostname_str, shard_name, "FUCKO")
        
        # run bin/get_index and store the result
        
        shard_name = subprocess.run(
            'bin/get_index',
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).stdout.decode('utf-8').strip()
        
        # format is vectordb-shard_service-<REPLICA_ID>.vectordb_app-network.
        # parse in order to get the replica id 
        
        logging.info("Shard name is %s", shard_name)
        
        match = re.search(r'-([0-9]+)\.vectordb_app-network', shard_name)

        if match:
            replica_id = match.group(1)
            logging.info("Replica ID is %s", replica_id)
            return int(replica_id)
        else:
            raise ValueError("Could not parse replica id") 
        
        

    def _get_ids(self):
        """
        
        Returns:
            tuple (int): cluster_id, shard_id, dimension
        """
        config_file = os.getenv('CONFIG_PATH', './config/config.yaml')
        config = parse_config(config_file)
        
        replica_id = self._get_replica_id()
        try:
            dimension = config['dimension']            
            nodes_per_cluster = config['nodes_per_cluster']
        except KeyError as e:
            click.echo(f"Configuration File {config_file} misconfigured. Missing key {e}")
            raise KeyError(f"Missing Key {e}")
        
        shard_id = replica_id % nodes_per_cluster
        cluster_id = replica_id // nodes_per_cluster
        
        return cluster_id, shard_id, dimension
        
        

    @DeprecationWarning
    def listen_for_coord(self):
        
        resp_channel = f'CoordinatorChannel'  
        
               
        for message in self.pubsub.listen():
            
            if message['type'] != 'message':
                continue

            # message_type = json.loads(message['type'])

            data = json.loads(message['data'].decode('utf-8'))
            # data = message['data']

                                
            future = self.executor.submit(self.exec_command, data) 
            
            try: 
                response = future.result()
                response['response_id'] = data['response_id']
                
                response = json.dumps(response).encode('utf-8')
                self.redis_client.publish(resp_channel, response)

            except Exception as e:
                print(e)
                self.redis_client.publish(resp_channel, {'status': 'error', 'message': str(e)})


    def process_coord_stream(self):
        stream_name = f'Cluster{self.cluster_id}Stream'
        response_stream = 'CoordinatorStream'
        consumer_name = f'shard_{self.shard_id}'
        consumer_group = f'shard_group_{self.shard_id}'
        
        
        # self.redis_client.xtrim(stream_name, 0)
        self.redis_client.delete(stream_name)
        try:
            self.redis_client.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP Consumer Group name already exists" in str(e):
                # logging.debug("Group already exists")
                pass
            else:
                raise e
        
        stream_pos = '>'
        
        while not self.shutdown:                
            
            entries = self.redis_client.xreadgroup(consumer_group, consumer_name, {stream_name: stream_pos}, count=1, block=1000)
            if not entries:
                continue
            
            for stream, entry in entries:
                if not entry:
                    continue
                
                message_id, message = entry[0]
                # logging.debug(f"Received Message: {message}")
                
                data = message[b'message'].decode('utf-8')
                data = json.loads(data)
                
                def process_message(data: dict, message_id: str):
                    try: 
                        response = self.exec_command(data)                        
                        response['response_id'] = data['response_id']
                        response['status'] = 'success'
                        response = json.dumps(response).encode('utf-8')
                        
                        self.redis_client.xadd(response_stream, {'message': response})
                    except Exception as e:
                        
                        response = {'status': 'error', 'message': str(e), 'response_id': data['response_id']}
                        response = json.dumps(response).encode('utf-8')

                        logging.error(e)                    
                        self.redis_client.xadd(response_stream, { 'message': response})
                    finally:
                        self.redis_client.xack(stream_name, consumer_group , message_id)
                        
                self.executor.submit(process_message, data, message_id)
                
        
    def exec_command(self, command: dict):        
        command_type = command['type']
        
        match command_type:
            case 'add_vector':
                return self.add_vectors(command['id'], np.array(command['vec']))            
            case 'get_vector':
                return self.get_vector(command['id'])
            case 'remove_vectors':
                return self.remove_vectors(command['ids'])
            case 'update_vectors':
                return self.update_vectors(command['ids'], command['vecs'])
            case 'search':
                return self.search(command['query'], command['k'])
            case 'save_index':
                pass
            case 'shutdown':
                self.shutdown()
                # does not return
            case _:
                raise ValueError(f"Invalid Command Type: {command_type}")

    # CRUD Operations

    def get_vector(self, id: str):
        with self.lock.reader_lock():
            try:
                vec = self.index.reconstruct(key=id)
                return {'status': 'success', 'vector': vec}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

    def get_vector_batch(self, ids: list[str]):
        with self.lock.reader_lock():
            try:
                vecs = self.index.reconstruct_batch(n=len(ids), keys=ids)
                return {'status': 'success', 'vectors': vecs}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

    def add_vectors(self, ids: list[int], vecs: np.ndarray[np.float64]):
        with self.lock.writer_lock():
            try: 
                self.index.add_with_ids(vecs, ids)
                return {'status': 'success'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
    
    
    def remove_vectors(self, ids_to_remove=list[str]):
        with self.lock.writer_lock():
            selector = faiss.IDSelectorArray(
                n=len(ids_to_remove), ids=ids_to_remove)

            try:
                self.index.remove_ids(selector)
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
            
        return {'status': 'success'}

    def update_vectors(self, ids=list[str], vecs=[np.ndarray]):
        with self.lock.wLock():
            try:
                self.remove_vectors(ids)
                self.add_vectors(ids, vecs)
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
            
        return {'status': 'success'}

    def search(self, query: np.ndarray, k: int):
        with self.lock.reader_lock():
            try:
                D, I = self.index.search(query, k)
                return {'status': 'success', 'distances': D, 'indices': I}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}
        
    def save_index(self):
        with self.lock.writer_lock():
            try:
                faiss.write_index(self.index, f'Cluster{self.cluster_id}Shard{self.shard_id}.index')
                return {'status': 'success'}
            except Exception as e:
                return {'status': 'error', 'message': str(e)}

    def monitor_leader_heartbeat(self):
        while not self.shutdown:
            leader_id = self.redis_client.get(self.LEADER_HEARTBEAT_KEY)                
            if leader_id is None:
                # no leader
                with self.leader_lock:
                    assert not self.is_primary
                    self.primary_id = None
                    self.failover()
            else:
                if leader_id != self.primary_id:
                    # leader has changed
                    with self.leader_lock:
                        self.primary_id = leader_id
                        self.is_primary = leader_id == self.shard_id
                else: 
                    # leader is the same
                    pass
            time.sleep(1)
            
            
    def failover(self) -> bool:
        """Try to become leader"""
        
        
        # Already have leader lock
        assert not self.is_primary
        assert self.leader_lock.locked()
        
        retries = 0
        while retries < 3:
            if self.redis_client.set(self.LEADER_HEARTBEAT_KEY, self.shard_id, nx=True, ex=DBShard.TIMEOUT_INTERVAL):
                self.is_primary = True
                self.primary_id = self.shard_id
                return True
            retries += 1
            time.sleep(1)
        return False

        
    
    def send_heartbeat(self):
        """SET the heartbeat key in redis every 0.5 seconds"""
        while True:
            # self.redis_client.set(self.HEARTBEAT_KEY, self.shard_id, ex=DBShard.TIMEOUT_INTERVAL)
            self.redis_client.expire(self.HEARTBEAT_KEY, DBShard.TIMEOUT_INTERVAL)
            with self.leader_lock:
                if self.is_primary:
                    # if primary, send distinct heart beat
                    # TODO: REFACTOR SO THAT PRIMARY DOES NOT HAVE A SPECIFIC HEARTBEAT
                    self.redis_client.expire(self.LEADER_HEARTBEAT_KEY, DBShard.TIMEOUT_INTERVAL)
                    
            time.sleep(0.5)
            
    def shutdown(self):
        """Shutdown the shard"""
        self.shutdown = True
        
        self.redis_client.delete(self.HEARTBEAT_KEY)
        self.redis_client.delete(self.LEADER_HEARTBEAT_KEY)
        self.redis_client.close()
        self.executor.shutdown()
        exit(0)
        

# Class to represents other shards in the cluster
class Replica:
    def __init__(self, id: int, is_primary: bool = False):
        self.shard_id = id
        self.is_leader = is_primary
        

    
    
@click.command()
# @click.option('--cluster_id', 'cluster_id', type=int, required=True)
# @click.option('--shard_id', 'shard_id', type=int, required=True)
# @click.option('--dimension', 'dimension',  type=int, required=True)
# @click.option('--shard_id', 'shard_id', type=int, required=True)
# @click.option('--primary_id', 'primary_id', type=int, required=True)
# @click.option('--other_shard_ids', 'other_shard_ids', type=str, default='', required=False)
def main():
    # other_shard_ids = [int(i) for i in other_shard_ids.split(',')]
    # other_shard_ids = list[int](other_shard_ids)
    # print(other_shard_ids)
    
    # if not config_file:
    #     raise ValueError("Config file not specificed")
    
    # config = parse_shard_config(config_file)
    
    # try:
    #     dimension = config['dimension']
    #     cluster_id = config['cluster_id']
    #     shard_id = int(config['shard_id'])
    #     primary_id = config['primary_id']
        
    #     other_shards_ids = [i for i in range()]
        
    # except KeyError as e:
    #     raise KeyError(f"Missing Key {e}")
    
    
    config_file = os.getenv('CONFIG_PATH', './config/config.yaml')
    config = parse_config(config_file)
    
    # try: 
    #     dimension = config['dimension']
    #     num_replicas_per_cluster = config['num_replicas_per_cluster']
    # except KeyError as e:
    #     raise KeyError(f"Missing Key {e}")    
    

    # try:
    #     cluster_id = int(os.getenv('CLUSTER_ID'))
    #     shard_id = int(os.getenv('SHARD_ID'))
    #     primary_id = int(os.getenv('PRIMARY_ID'))
    # except Exception as e:
    #     # raise ValueError(f"Invalid Environment Variables: {e}")
    #     click.echo(f"Invalid Environment Variables: CLUSTER_ID, SHARD_ID, PRIMARY_ID")
    #     exit(1)
    
    # other_shard_ids = [i for i in range(num_replicas_per_cluster + 1) if i != shard_id]
    
    DBShard()
    while True:
        time.sleep(1)    
    

if __name__ == '__main__':
    main()


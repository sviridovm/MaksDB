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


logging.basicConfig(level=logging.DEBUG, format='%(threadName)s: %(message)s')
class DBShard:
    TIMEOUT_INTERVAL = 5
    
    
    def __init__(self, dimension: int, cluster_id: int, shard_id: int, primary_id: int, other_shard_ids: list[int] = []):
        """
        Args:
            dimension (int): Dimension of the vectors
            cluster_id (int): Cluster id that the shard belongs to
            shard_id (int): Id of the shard, must be unique within the cluster
            primary_id (int): Id of the primary shard
            other_shard_ids (list[int]): List of ids of other shards in the cluster
        """
        
        
        index = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexIDMap2(index)
        self.lock = rwLock()
        self.cluster_id = cluster_id
        self.redis_client = redis.Redis()
        self.leader_lock = Lock()


        self.HEARTBEAT_KEY = f'Cluster{cluster_id}Shard{shard_id}Heartbeat'
        self.LEADER_HEARTBEAT_KEY = f'Cluster{cluster_id}LeaderHeartbeat'
        self.redis_client.set(self.HEARTBEAT_KEY, shard_id, ex=DBShard.TIMEOUT_INTERVAL)


        self.shard_id = shard_id
        self.primary_id = primary_id
        self.is_primary = shard_id == primary_id

        if self.is_primary:
            self.redis_client.set(self.LEADER_HEARTBEAT_KEY, primary_id, ex=DBShard.TIMEOUT_INTERVAL)


        # list of replicas in the shard
        self.replicas = [Replica(i, i == primary_id) for i in other_shard_ids if i != shard_id]
        

        self.executor = ThreadPoolExecutor(max_workers=10)
        
        
        self.heartbeat_thread = Thread(target=self.send_heartbeat, daemon=True).start()
        
        self.monitor_leader_thread = Thread(target=self.monitor_leader_heartbeat, daemon=True).start()
        self.listen_thread = Thread(target = self.process_coord_stream).start()


        
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
        
        
        self.redis_client.xtrim(stream_name, 0)
        try:
            self.redis_client.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP Consumer Group name already exists" in str(e):
                # logging.debug("Group already exists")
                pass
            else:
                raise e
        
        stream_pos = '>'
        
        while True:                
            
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
                        response = json.dumps(response).encode('utf-8')
                        
                        self.redis_client.xadd(response_stream, {'message': response})
                    except Exception as e:
                        logging.error(e)                    
                        self.redis_client.xadd(response_stream, {'status': 'error', 'message': str(e)})
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
        while True:
            leader_id = self.redis_client.get(self.LEADER_HEARTBEAT_KEY)                
            if leader_id is None:
                # no leader
                with self.leader_lock:
                    assert not self.is_primary
                    self.is_primary = False
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
@click.option('--dimension', 'dimension',  type=int, required=True)
@click.option('--cluster_id', 'cluster_id', type=int, required=True)
@click.option('--shard_id', 'shard_id', type=int, required=True)
@click.option('--primary_id', 'primary_id', type=int, required=True)
@click.option('--other_shard_ids', 'other_shard_ids', type=str, default='', required=False)
def main(dimension, cluster_id, shard_id, primary_id, other_shard_ids):
    other_shard_ids = [int(i) for i in other_shard_ids.split(',')]
    # other_shard_ids = list[int](other_shard_ids)
    # print(other_shard_ids)
    
    DBShard(dimension, cluster_id, shard_id, primary_id, other_shard_ids)
    while True:
        time.sleep(1)    
    

if __name__ == '__main__':
    main()


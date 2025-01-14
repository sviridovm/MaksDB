import time
import click
import faiss
import numpy as np
import json_tricks as json
import redis.client
import warnings
import threading
from threading import Thread
import redis
from concurrent.futures import ThreadPoolExecutor, Future
import logging 
import os

logging.basicConfig(level=logging.DEBUG, format='%(threadName)s: %(message)s')


def bruh(text: str):
    FILE = 'var/bruh.txt'
    with open(FILE, 'a') as f:
        f.write(text + '\n')

class DBShardMomma:
    COMMAND_CHANNEL = "coordinator_commands"
    
    def __init__(self, dimension: int, num_clusters: int = 10, random_centroids=True, random_seed=None, redis_host='localhost', redis_port=6379):
        if random_centroids and not random_seed:
            warnings.warn("Random centroids have irreproducible behaviour")

        if random_seed:
            np.random.seed(random_seed)

        self.d = dimension
        self.num_clusters = num_clusters

        num_random_training_vecs = 1000
        random_vecs = np.random.random((num_random_training_vecs, dimension)).astype('float32')

        # self.kmeans = faiss.Kmeans(self.d, num_clusters,
                            #   niter=20, verbose=True)
        # self.kmeans.train(random_vecs)

        self.quantizer = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexIVFFlat(self.quantizer, dimension, num_clusters, faiss.METRIC_L2)
        self.index.train(random_vecs)
    


        # self.index = faiss.IndexIVFFlat(
        # self.quantizer, self.d, num_clusters, faiss.METRIC_L2)
        # self.index.quantizer = kmeans
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.executor = ThreadPoolExecutor(max_workers=num_clusters)
                
        self.responses = {}
        self.responses_lock = threading.Lock()
        
        # self.api_thread = Thread(target=self.listen_for_api, daemon=False).start()
        Thread(target=self.listen_for_shard_resps, daemon=True).start()


    def listen_for_shard_resps(self):
        # resp_channel = f'CoordinatorChannel' 
        stream_name = 'CoordinatorStream'
        consumer_group = 'CoordinatorGroup'
        consumer_name = 'Coordinator'

        
        # self.redis_client.xtrim(stream_name, 0)
        self.redis_client.delete(stream_name)
        
        try:
            self.redis_client.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP Consumer Group name already exists" in str(e):
                logging.debug("Group already exists")
                # self.redis_client.delete(stream_name)
                pass
            else:
                raise e
        
        
        while True:
            try:
                entries = self.redis_client.xreadgroup(consumer_group, consumer_name, {stream_name: '>'}, count=1, block=0)
                if not entries:
                    continue
                
                for stream, entry in entries:
                    message_id, message = entry[0]

                    data = json.loads(message[b'message'].decode('utf-8'))

                    response_id = data.pop('response_id')
                    
                    with self.responses_lock:
                        if response_id in self.responses:
                            future = self.responses.pop(response_id)
                            future.set_result(data)

                    self.redis_client.xack(stream_name, consumer_group, message_id)
            except Exception as e:
                logging.error(e)
                raise e

    @DeprecationWarning
    def publish_msg(self, shard_id: int, message: str):
        channel = f'Channel{shard_id}'        
        self.redis_client.publish(channel, message)
        
    def add_msg_to_stream(self, cluster_id: int, message: str):
        stream = f'Cluster{cluster_id}Stream'
        # logging.debug(f'Adding message to stream {stream}')
        
        try:
            entry_id = self.redis_client.xadd(stream, {'message': message})
            logging.debug(f'Added message to stream {stream} with entry id {entry_id}')
        except Exception as e:
            logging.error(e)    
    
        
    def exec_command(self, command: dict, cluster_ids: list[int], timeout=10):
        # generate response id based on thread that handles the request
        response_id = threading.get_ident()
        command['response_id'] = response_id
        
        # value that will be populated when the response is received
        future_response = Future()
        
        with self.responses_lock:
            self.responses[response_id] = future_response

        # send msg to shard
        for cluster_id in cluster_ids:
            try:
                msg = json.dumps(command).encode('utf-8')
            except Exception as e:
                print(e)
                raise e
            
            # self.publish_msg(shard_id, msg)
            self.add_msg_to_stream(cluster_id, msg)


        # wait for response
        return future_response.result(timeout=timeout)

    
    def shutdown(self):
        """Tell the coordinator to shutdown"""
        # !TODO: How to get shutdown message from cli?
        for response in self.responses.values():
            response.cancel()
        
        command = {'type': 'shutdown'}
        for cluster_id in range(self.num_clusters):
            stream = f'Cluster{cluster_id}Stream'
            # self.redis_client.delete(stream)
            self.add_msg_to_stream(cluster_id, json.dumps(command).encode('utf-8'))

        self.redis_client.close()
        self.executor.shutdown()
        

    def add_vector(self, vector_id: int, vector: np.ndarray):
        vec = np.reshape(vector, (1, -1))
        
        try :
            cluster_ids = self.index.quantizer.assign(vec, k = 1)[0]
        except Exception as e:
            # return Future().set_result(str(e))
            return self.executor.submit(str, e)
            raise e
        
        
        bruh(f"ADDING IN CLUSTERS { cluster_ids}")
            
            
        command = {'type': 'add_vector', 
                   'id': [vector_id], 
                   'vec': vec}
        
        return self.executor.submit(self.exec_command, command, cluster_ids)
        
    # def add_vectors(self, vector_ids: list[int], vectors: np.ndarray):
        
    def search(self, query: np.ndarray, k: int):
        query = np.reshape(query, (1, -1))

        cluster_ids = self.index.quantizer.assign(query, k = 1)[0]
        bruh(f"SEARCHING IN CLUSTERS { cluster_ids}")
        
        
        command = {'type': 'search',
                   'query': query,
                   'k': k}
        
        return self.exec_command(command, cluster_ids)        
    
    # def get_vector(self, vector_id: int):
    #     command = {'type': 'get_vector', 
    #                'id': vector_id}
        
    #     return self.exec_command(command, [0])

    @DeprecationWarning
    def listen_for_api(self):
        pubsub = self.redis_client.pubsub(
            ignore_subscribe_messages=True
        )
        pubsub.subscribe(self.COMMAND_CHANNEL)
        RESPONSE_CHANNEL = "coordinator_responses"
                
        # self.redis_client.publish(RESPONSE_CHANNEL, 'Coordinator is ready')

        api_executor = ThreadPoolExecutor(max_workers=None)
    
        while True:
            for message in pubsub.listen():      
                if message['type'] != 'message':
                    continue                
                
                # print(message)
                data = json.loads(message['data'].decode('utf-8'))
                # print(data)
                command_id = data['id']
                
                # self.redis_client.publish(RESPONSE_CHANNEL, json.dumps({'id': command_id, 'data': 'received'}))
                
                def handle_command(data):
                    match data['type']:
                        case 'add_vector':
                            vector_id = data['vec_id']
                            vector = data['vec']
                            return self.add_vector(vector_id, vector)
                        case 'search':
                            query = data['query']
                            k = data['k']
                            return self.search(query, k)
                        case 'shutdown':
                            return self.shutdown()
                        case _:
                            pass
                        
                def callback(future: Future):
                    result = future.result()
                    print('5' * 50)
                    print(result)
                    print('5' * 50)
                    
                    
                    print("FUTURE US FUCKING RUNNING DURING THE CALLBAC BECAUSE OF SOME BULLSHIT")
                    self.redis_client.publish(RESPONSE_CHANNEL, json.dumps({'id': command_id, 'data': result}).encode('utf-8'))
                
                with api_executor as executor:
                    future = executor.submit(handle_command, data)
                    future.add_done_callback(
                        callback
                    )



@click.command()
# @click.option('--dimension', 'dimension', type=int, required=True)
# @click.option('--num_clusters', 'num_clusters', type=int, required=True)
@click.option('--config', 'config', type=str, required=True)
def main(config: str):
    from vectordb.utils.config_parser import parse_config
    
    config = parse_config(config)
    
    try:
        dimension = config.get('dimension')
        num_clusters = config.get('num_clusters')
    except KeyError as e:
        print(f"Missing key in config file: {e}")
        raise e
    
    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')
    
    click.echo(f"Starting coordinator with dimension {dimension} and {num_clusters} clusters")
    exit()
    
    shard = DBShardMomma(
        dimension=dimension, 
        num_clusters=num_clusters,
        redis_host=redis_host,
        redis_port=redis_port
        )
    
    while True:
        time.sleep(1)    
    

if __name__ == '__main__':
    main()
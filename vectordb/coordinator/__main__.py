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



class DBShardMomma:
    def __init__(self, dimension: int, num_clusters: int = 10, random_centroids=True, random_seed=None):
        if random_centroids and not random_seed:
            warnings.warn("Random Centroids has Irreproducible behaviour")

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
        self.redis_client = redis.Redis()
        self.executor = ThreadPoolExecutor(max_workers=num_clusters)
        
        self.responses = {}
        self.responses_lock = threading.Lock()
        
        
        Thread(target=self.listen_for_shard_resps, daemon=True).start()

        # Do not have access to shards in distributed model
        # self.shards = [DBShard(dimension=self.d) for _ in range(num_clusters)]

    def listen_for_shard_resps(self):
        resp_channel = f'CoordinatorChannel' 
        
        pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(resp_channel)

        # while True:
        for message in pubsub.listen():
            # if message['type'] == 'message':
                # message = pubsub.get_message()
                if message is None:
                    continue

                data = json.loads(message['data'].decode('utf-8'))


                response_id = data.pop('response_id')
                
                with self.responses_lock:
                    if response_id in self.responses:
                        future = self.responses.pop(response_id)
                        future.set_result(data)

    def publish_msg(self, shard_id: int, message: str):
        channel = f'Channel{shard_id}'        
        self.redis_client.publish(channel, message)
        
    def exec_command(self, command: dict, shard_ids: list[int], timeout=10):
        # generate response id based on thread that handles the request
        response_id = threading.get_ident()
        command['response_id'] = response_id
        
        # value that will be populated when the response is received
        future_response = Future()
        
        with self.responses_lock:
            self.responses[response_id] = future_response

        # send msg to shard
        for shard_id in shard_ids:
            try:
                msg = json.dumps(command).encode('utf-8')
            except Exception as e:
                print(e)
            
            self.publish_msg(shard_id, msg)


        # wait for response
        return future_response.result(timeout=timeout)


    def add_vector(self, vector_id: int, vector: np.ndarray):
        vec = np.reshape(vector, (1, -1))
        cluster_ids = self.index.quantizer.assign(vec, k = 1)[0]
            
        command = {'type': 'add_vector', 
                   'id': vector_id, 
                   'vec': vec}
        
        return self.executor.submit(self.exec_command, command, cluster_ids)
        
    # def add_vectors(self, vector_ids: list[int], vectors: np.ndarray):
        
    def search(self, query: np.ndarray, k: int):
        query = np.reshape(query, (1, -1))

        cluster_ids = self.index.quantizer.assign(query, k = 1)[0]
        
        command = {'type': 'search',
                   'query': query,
                   'k': k}
        
        return self.exec_command(command, cluster_ids)        
    
    # def get_vector(self, vector_id: int):
    #     command = {'type': 'get_vector', 
    #                'id': vector_id}
        
    #     return self.exec_command(command, [0])




@click.command()
@click.option('--dimension', 'dimension', type=int, required=True)
@click.option('--num_clusters', 'num_clusters', type=int, required=True)
def main(dimension, num_clusters):
    shard = DBShardMomma(dimension=dimension, num_clusters=num_clusters)
    while True:
        time.sleep(1)    
    

if __name__ == '__main__':
    main()
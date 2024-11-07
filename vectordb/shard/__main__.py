import time
import click
import faiss
import numpy as np
import json_tricks as json
import redis.client
from vectordb.utils.rw_lock import rwLock
from threading import Thread
import redis
from concurrent.futures import ThreadPoolExecutor, Future

class DBShard:
    def __init__(self, dimension: int, id: int):
        index = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexIDMap2(index)
        self.lock = rwLock()
        self.shard_id = id
        self.redis_client = redis.Redis()
        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(f'Channel{id}')
        print("LISTENING ON CHANNEL ", f'Channel{id}')

        self.executor = ThreadPoolExecutor(max_workers=10)

        self.listen_thread = Thread(target = self.listen_for_coord, daemon=True).start()

        
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
            case _:
                raise ValueError(f"Invalid Command Type: {command_type}")

    def save_index(self):
        faiss.write_index(self.index, f"index_{self.id}.index")


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

    def add_vectors(self, ids: list[str], vecs: np.ndarray[np.float64]):
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
        self.save_index()
        
        
@click.command()
@click.option('--dimension', 'dimension',  type=int, required=True)
@click.option('--shard_id', 'shard_id', type=int, required=True)
def main(dimension, shard_id):
    shard = DBShard(dimension, shard_id)
    while True:
        time.sleep(1)    
    

if __name__ == '__main__':
    main()


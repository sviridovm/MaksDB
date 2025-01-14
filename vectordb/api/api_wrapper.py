import requests
import requests_async

class MaksDB:
    
    def __init__(self, port: int = 1256, host: str = 'localhost', redis_host: str = 'localhost', redis_port: int = 6379):
        self.port = port
        self.host = host
        self.redis_host = redis_host
        self.redis_port = redis_port
        

    def add_vector_sync(self, vector: list[float], vector_id: int):
        res = requests.post(f'http://{self.host}:{self.port}/add', json={'vector': vector, 'vector_id': vector_id})
        return res
    
    def search_sync(self, query: list[float], k: int):
        res = requests.get(f'http://{self.host}:{self.port}/search', json={'query': query, 'k': k})
        return res    
    
    def test(self):
        return requests.get(f'http://{self.host}:{self.port}/')
    
    async def add_vector(self, vector: list[float], vector_id: int):
        response = await requests_async.post(f'http://{self.host}:{self.port}/add', json={'vector': vector, 'vector_id': vector_id})
        return response
        
        # return requests.post(f'http://{self.host}:{self.port}/add', json={'vector': vector, 'vector_id': vector_id})
    
    # def stop(self):
    

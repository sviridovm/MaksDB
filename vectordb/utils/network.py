import redis



class Network:
    """Create an abstraction layer for handling redis streams"""

    def __init__(self):
        self.redis_client = redis.Redis()
        # self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        
    
    def receive_msg(self, stream):
        """Receive a message from a stream"""
        return self.redis_client.xread({stream: '0-0'}, count=1, block=0)
    
    def send_msg(self, stream, message):
        """Send a message to a stream"""
        self.redis_client.xadd(stream, message)
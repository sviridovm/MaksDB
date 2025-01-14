import click
from fastapi import FastAPI, HTTPException, Depends
from concurrent.futures import Future
import numpy as np
import redis
import uuid
import json_tricks as json
from vectordb.utils.types import AddVectorRequest, SearchRequest
import time
import pydantic
from vectordb.coordinator import DBShardMomma
from vectordb.utils.config_parser import parse_config
import os

app = FastAPI()

config = parse_config("config/config.yaml")

try:
    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    dimension = config.get("dimension")
    num_clusters = config.get("num_clusters")
except Exception as e:
    print(f"Missing key in config file: {e}")
    raise e
    # exit(1)

coordinator = DBShardMomma(dimension=dimension, num_clusters=num_clusters, redis_host=redis_host, redis_port=redis_port)

# coordinator = DBShardMomma(
#     dimension=dimension, 
#     num_clusters=num_clusters,
#     redis_host=redis_host,
#     redis_port=redis_port
#     )


@app.get("/")
def root():
    return {"message": "Hello World"}

# @app.post("/init")
# def root(InitParams: InitParams):

#     if shared_state["coordinator"]:
#         return {"error": "coordinator already initialized"}
    
#     shared_state["coordinator"] = DBShardMomma(dimension=InitParams.dimension, num_clusters=InitParams.num_clusters)
#     return {"bruh": "moment"}
    
@app.api_route("/shutdown", methods=["POST", "GET"])
def shutdown():
    try: 
        coordinator.shutdown()
        return {"message": "Shutting down"}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/search")
def search(request: SearchRequest):
    vec = np.array(request.query)
    
    try:
        return coordinator.search(vec, request.k).result()
    except Exception as e:
        return {"error": str(e)}


@app.post("/add")
def add(request: AddVectorRequest):
    
    vec = np.array(request.vector)
    
    try:
        res = coordinator.add_vector(vec, request.vector_id).result()
        # print(res)
        return res
    except Exception as e:
        return {"error": str(e)}



# @click.command()
# @click.option('--config', 'config', type=str, required=True)
def main():
        
    try:
        api_host = config['api_host']
        api_port = config['api_port']

    except KeyError as e:
        print(f"Missing key in config file: {e}")
        raise e
    
    import uvicorn
    uvicorn.run(app, host=api_host, port=api_port)
    

if __name__ == "__main__":
    main()

# Channel names
# COMMAND_CHANNEL = "coordinator_commands"
# RESPONSE_CHANNEL = "coordinator_responses"

# @DeprecationWarning
# def get_response(command: dict, command_id: str, timeout: int = 10):
#     pubsub = redis_client.pubsub(
#         ignore_subscribe_messages=True
#     )
#     pubsub.subscribe(RESPONSE_CHANNEL)
    
#     json_command = json.dumps(command)
#     redis_client.publish(COMMAND_CHANNEL, json_command.encode("utf-8"))
    
#     initial_time = time.time()

#     while True:
#         for message in pubsub.listen():
#             if message["type"] != "message":
#                 continue
#             print(message)
#             if message["type"] == "message":
#                 response = json.loads(message["data"].decode("utf-8"))
#                 if response["id"] == command_id:
#                     pubsub.unsubscribe()
#                     return {response["data"]}
            
#     raise HTTPException(status_code=500, detail="No response received")
import click
import subprocess
import yaml
import os
import signal
import requests
import time
import docker

def worker_options(func):
    func = click.option('--cluster_id', 'cluster_id', type=int, required=True)
    func = click.option('--shard_id', 'shard_id', type=int, required=True)
    func = click.option('--primary_id', 'primary_id', type=int, required=True)
    func = click.option('--other_shard_ids', 'other_shard_ids', type=str, default='', required=False)
    return func

@click.group()  
def cli():
    pass

def load_config(config_file: str = "config/config.yaml"):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        return config

def manage_images(rebuild: bool, image_name: str):
    docker_client = docker.from_env()
    if rebuild:
        docker_client.images.build(path='.', tag=image_name)
    else:
        try:
            docker_client.images.get(image_name)
        except docker.errors.ImageNotFound:
            docker_client.images.build(path='.', tag=image_name)
            
    
HOST = 'localhost'
PORT = 1256

@cli.command()
# @click.option('--num_replicas_per_cluster', 'num_replicas', type=int, required=True)
@click.option('--config_file', 'config_file', type=str, required=False, default='config/config.yaml')
@click.option('--rebuild', 'rebuild', type=bool, required=False, default=False)
def start(config_file: str, rebuild: bool):
    """Start the coordinator and workers"""
    # check for running containers
    # docker_client = docker.from_env()
    # coord_containers = docker_client.containers.list(filters={'label': 'app=maksdb-coordinator'})
    # shard_containers = docker_client.containers.list(filters={'label': 'app=maksdb-shard'})
    # containers = coord_containers + shard_containers
    
    # if len(containers) > 0:
    #     click.echo("Coordinator and workers are already running")
    #     click.echo("Consider running maksdb stop to stop the running containers")
    #     return
    
    
    
    
    SHARD_IMAGE = 'shard_image'
    COORDINATOR_IMAGE = 'coordinator_image'
    
    # build images, if necessary
    # manage_images(rebuild, SHARD_IMAGE)        
    # manage_images(rebuild, COORDINATOR_IMAGE)
    
    # process configs file
    try : 
        config = load_config(config_file)
    except FileNotFoundError as e:
        click.echo(f"Config file not found: {config_file}")
        raise e
    
    try: 
        num_clusters = config['num_clusters']
        dimension = config['dimension']
        nodes_per_cluster = config['nodes_per_cluster']
        # global HOST
        # HOST = config['api_host']
        # global PORT
        # PORT = int(config['api_port'])
    except KeyError as e:
        click.echo(f"Missing key in config file: {e}")
        raise e
    

    
    # start coordinator
    # docker_client.containers.run(
    #     image=COORDINATOR_IMAGE,
    #     command=f'server',
    #     detach=True,
    #     remove=True,
    #     name='Coordinator',
    #     labels={'app' : 'maksdb-coordinator'}
    # )
    
    
    #---------------------------------------------------
    subprocess.run(["docker-compose", "up", "coordinator_service", "-d"])
    
    subprocess.run([
                "docker-compose",
                "up",
                "shard_service",
                "--scale",
                f"shard_service={nodes_per_cluster * num_clusters}",
                "-d"
            ])
    
    # ---------------------------------------------------
    
    
    #! NEW FOR DOCKER SWARM
    #? nvm I guess
    # subprocess.run(["docker", "stack", "deploy", "coordinator_service", "-c", "docker-compose.yml"])

    
    # subprocess.run(["docker", "stack", "deploy", "-c", "docker-compose.yml", "shard_service"])

    # subprocess.run([
    # "docker",
    # "service",
    # "update",
    # "--replicas=" + str(nodes_per_cluster * num_clusters),
    # "shard_service"
    # ])
    
    # worker_ids = list(range(num_replicas_per_cluster + 1))
    # worker_ids_str = ','.join(str(worker_id) for worker_id in worker_ids)
    
    # start workers
    # for cluster_id in range(num_clusters):
        # for shard_id in range(num_replicas_per_cluster + 1):
            # docker_client.containers.run(
            #     image=SHARD_IMAGE,
            #     command=f'shard --dimension {dimension} --cluster_id {cluster_id} --shard_id {shard_id} --primary_id 0 --other_shard_ids {worker_ids_str}',
            #     detach=True,
            #     remove=True,
            #     labels={'app' : 'maksdb-shard'},
            #     name=f'Cluster{cluster_id}Shard{shard_id}'
            # )
            
            # os.environ['CLUSTER_ID'] = str(cluster_id)
            # os.environ['SHARD_ID'] = str(shard_id)
            
            
            
            # processes.append(shard_process)   
    
    
    # with open('var/running_pids.txt', 'w') as f:
    #     for process in processes:
    #         f.write(str(process.pid) + '\n')
        
  #TODO:  End previous REDIS server
  
    # START redis
    # os.system("redis-server")
    # subprocess.Popen(['redis-server'], start_new_session=True, stdout=subprocess.DEVNULL)
    
   
    click.echo("Started coordinator and workers")
    # click.echo(f"Started FASTAPI server at http://{HOST}:{PORT}")
    
@cli.group()
def submit():
    """Submit a job to the coordinator"""
    pass


# @submit.command()
# def search(query: list[float], k: int):
#     """Submit a search job"""
#     # send a post request to the API
    
#     res = requests.post(f'http://{HOST}:{PORT}/search', json={'query': query, 'k': k})
#     print(res)

@submit.command()
def search_test():
    """Submit a search job"""
    
    a = requests.post(f'http://{HOST}:{PORT}/init', json={'dimension': 4, 'num_clusters': 1})
    print(a)
    res = requests.post(f'http://{HOST}:{PORT}/search', json={'query': [1, 0, 0, 1], 'k': 1}, timeout=10)
    print(res.json())

@submit.command()
def add():
    """Submit an add job"""
    res = requests.post(f'http://{HOST}:{PORT}/add', json={'vector': [1, 0, 0, 1], 'vector_id': 1})
    print(res)
    
@submit.command()
def add_test():
    """Submit an add job"""
    
    res = requests.post(f'http://{HOST}:{PORT}/add', json={'vector': [1, 0, 0, 1], 'vector_id': 1}, timeout=10)
    print(res)    
    
    
    
@cli.command()
def stop():
    """ Tell the coordinator to shutdown"""
    try:
        res = requests.post(f'http://{HOST}:{PORT}/shutdown')
        print(res)
    except Exception as e:
        print(e)
        
    

# @cli.command()
# def stop():
#     """Tell the coordinator to shutdown"""
#     with open('var/running_pids.txt', 'r') as f:
#         pids = [int(pid.strip()) for pid in f.readlines()]

#     for pid in pids:
#         try:
#             os.kill(pid, signal.SIGTERM)  # Send the termination signal
#             # click.echo(f"Stopped process with PID {pid}")
#         except ProcessLookupError:
#             # click.echo(f"Process with PID {pid} not found. It may have already stopped.")
#             pass

#     # STOP FAST API server
#     result = subprocess.run(
#         ['lsof', '-ti', f':{PORT}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
#     )
    
#     api_pids = result.stdout.decode('utf-8').strip().split('\n')
#     # print(api_pids)

#     for pid in api_pids:
#         if pid != '':
#             os.kill(int(pid), signal.SIGKILL)


#     open('var/running_pids.txt', 'w').close()
    
    # STOP FASTAPI server
    # os.system("pkill uvicorn")
    

# @cli.command()
# @worker_options
# def start_worker(cluster_id, shard_id, primary_id, other_shard_ids):
    
    

# for packaging purposes 
if __name__ == '__main__':
    cli()    



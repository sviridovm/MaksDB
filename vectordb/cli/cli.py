import click
from vectordb.coordinator.__main__ import main as coordinator_main
import subprocess
import yaml
import os
import signal

def worker_options(func):
    func = click.option('--cluster_id', 'cluster_id', type=int, required=True)
    func = click.option('--shard_id', 'shard_id', type=int, required=True)
    func = click.option('--primary_id', 'primary_id', type=int, required=True)
    func = click.option('--other_shard_ids', 'other_shard_ids', type=str, default='', required=False)
    return func

@click.group()  
def cli():
    pass



@cli.command()
# @click.option('--num_replicas_per_cluster', 'num_replicas', type=int, required=True)
@click.option('--config_file', 'config_file', type=str, required=True)
def start(config_file):
    with open('var/running_pids.txt', 'r') as f:
        pids = [int(pid.strip()) for pid in f.readlines()]
        
    if len(pids) > 0:
        click.echo("Coordinator and workers are already running")
        return
    
    
    processes = []
    
    # process configs file
    config = load_config(config_file)
    num_clusters = config['num_clusters']
    dimension = config['dimension']
    
    # start coordinator
    coord_process = subprocess.Popen(['coordinator', 
                                      '--dimension', str(dimension), 
                                      '--num_clusters', str(num_clusters)], 
                                     start_new_session=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)      
    processes.append(coord_process)
    
    num_replicas_per_cluster = config['num_replicas_per_cluster']
    worker_ids = list(range(num_replicas_per_cluster + 1))
    worker_ids_str = ','.join(str(worker_id) for worker_id in worker_ids)
    
    # start workers
    for cluster_id in range(num_clusters):
        for shard_id in range(num_replicas_per_cluster + 1):
            shard_process = subprocess.Popen(
                ['shard', 
                 '--dimension', str(dimension),
                 '--cluster_id', str(cluster_id), 
                 '--shard_id', str(shard_id), 
                 '--primary_id', str(0), 
                 '--other_shard_ids', str(worker_ids_str)],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            processes.append(shard_process)   
    
    
    with open('var/running_pids.txt', 'w') as f:
        for process in processes:
            f.write(str(process.pid) + '\n')
        
    click.echo("Started coordinator and workers")
    
    
@cli.command()
def stop():
    """Tell the coordinator to shutdown"""
    with open('var/running_pids.txt', 'r') as f:
        pids = [int(pid.strip()) for pid in f.readlines()]

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)  # Send the termination signal
            # click.echo(f"Stopped process with PID {pid}")
        except ProcessLookupError:
            # click.echo(f"Process with PID {pid} not found. It may have already stopped.")
            pass

    open('var/running_pids.txt', 'w').close()
    
def load_config(config_file: str = "config/config.yaml"):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        return config

# @cli.command()
# @worker_options
# def start_worker(cluster_id, shard_id, primary_id, other_shard_ids):
    
    

# for packaging purposes 
if __name__ == '__main__':
    cli()    



# MaksDB

A Sharded Vector DB implemented with [FAISS](https://github.com/facebookresearch/faiss).

MaksDB partitions its shards based on K-Means Clusters. Users have an option to create the K-Means clusters based on supplied data or have them initialized with random vectors.

Each shard maintains an L2 Flat Index, with support for querying vectors by IDs. Each shard can be optionally represented with a Primary Replica Model, which uses Lease based leadership election and Write-Ahead Logging (in progress) to maintain weak consistency.  

MaksDB uses Redis Streams to ensure consistent inter-process communication and Redis Key-Value store to implement the lease based leadership model. MaksDB is highly concurrent, allowing concurrent reads and writes whenever possible.

Package management is managed by [Poetry](https://python-poetry.org/)

Planned Updates:

- Create a REST/gRPC api to interface with coordinator process remotely
- Implement WAL for replication. Currently replicas only monitor state of primary
- Dynamic Centroid Initialization
- Multiprobing and Redudant Storing

Usage Through CLI (WIP):

```bash
        poetry install
        redis-server
        maksdb start
        maksdb stop
```

Usage Through Python Interface:

:warning: **WARNING:**  ⚠️ Soon to be deprecated.
  
```python
import time
from vectordb.shard import DBShard
from vectordb.coordinator import DBShardMomma
import numpy as np

num_clusters = 2
# create coordinator
db = DBShardMomma(dimension=4, num_clusters=2, random_seed=1228)
shards = []

# create shards
for i in range(num_clusters):
        shards.append(DBShard(dimension=4, cluster_id=i, shard_id=0, primary_id=0))

# add 10 random vectors
results = []
for _ in range(10):
        res = db.add_vector(1, np.random.random((4,)).astype('float32'))
        # res is of type concurrent.Futures
        results.append(res)
        
# just to ensure log messages do not interfere with output
time.sleep(2)

# See Results
for i, res in enumerate(results):
print(i, res.result())
```

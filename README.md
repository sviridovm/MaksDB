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

Usage:

```bash
        poetry install
        maksb start
        maksb stop
```

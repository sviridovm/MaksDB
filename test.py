import time
from vectordb.shard import DBShard
from vectordb.coordinator import DBShardMomma
import numpy as np
    
def main():
    # test coordinator
    
    num_clusters = 2
    db = DBShardMomma(dimension=4, num_clusters=2, random_seed=1228)
    shards = []

    for i in range(num_clusters):
        shards.append(DBShard(dimension=4, id=i))


    results = []
    for _ in range(100):
        res = db.add_vector(1, np.random.random((4,)).astype('float32'))
        results.append(res)
        
    print("response is")
    print("________________________")
    # print(res)
    
    time.sleep(2)
    
    for i, res in enumerate(results):
        print(i, res.result())
        # assert res.result()['status'] == 'success'
    

if __name__ == "__main__":
    main()  
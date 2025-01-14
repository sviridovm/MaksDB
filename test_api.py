from vectordb.api.api_wrapper import MaksDB
import numpy as np
import asyncio

db = MaksDB()


def main():

    print(db.test().json())


    for i in range(1):
        res = db.add_vector_sync(vector=np.random.random((4,)).astype('float32').tolist(), vector_id=i)
        print(res.json())
        
    vec = np.random.random((4,)).astype('float32').tolist()
    
    print('-' * 50)
    res = db.search_sync(query=vec, k=5)
    print(res.json())       


if __name__ == "__main__":
    # asyncio.run(main())
    main()
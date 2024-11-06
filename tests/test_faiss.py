import faiss
import numpy as np

np.random.seed(1228)

d = 4
num_cluster = 10

quantizer = faiss.IndexFlatL2(d)
index = faiss.IndexIVFFlat(quantizer, d, num_cluster, faiss.METRIC_L2)

# Train index on some representative dataset (required before adding)
training_vectors = np.random.random((400, d)).astype(
    'float32')  # 1000 training vectors
index.train(training_vectors)
# index.set_direct_map_type(faiss.DirectMap.Array)


assert index.is_trained

new_vecs = np.random.random((400, d)).astype('float32')
# index.add(new_vecs)

# vec = [1] * 16
# print(training_vectors)


vec = np.random.random((1, d)).astype('float32')
vec = np.reshape(vec, (1, -1))

cluster_ids = index.quantizer.assign(vec, k=3)

print(index.nlist)

print(cluster_ids)

# for id in cluster_ids:
#     v = index.reconstruct(id)
#     print(v)


from annoy import AnnoyIndex
import numpy as np
import os


class VectorDB:
    def __init__(self, src_path: str = None, vector_size: int = None, metric: str = 'angular', n_trees=10, dest_path: str = None):
        if src_path:
            # check that filename exsists

            if not os.path.exists(src_path):
                raise ValueError(f"File {src_path} does not exist")

            self.annoy_index = AnnoyIndex(vector_size, metric=metric)
            self.annoy_index.load(src_path)
            self.vector_size = vector_size
            self.metric = metric

            if dest_path:
                self.dest_path = dest_path
            else:
                self.dest_path = src_path

            self.n_trees = self.annoy_index.get_n_trees()
            self.index_built = True
        else:
            self.vector_size = vector_size
            self.metric = metric
            self.n_trees = n_trees
            self.index_built = False
            self.annoy_index = AnnoyIndex(vector_size, metric)
            self.dest_path = dest_path

    def add_vector(self, vector_id: int, vector: np.ndarray):
        if len(vector) != self.vector_size:
            raise ValueError(
                'Vector size does not match the vector size of the database')

        self.annoy_index.add_item(vector_id, vector)

    def build_index(self):
        self.annoy_index.build(self.n_trees)
        self.index_built = True

    def save_index(self, filepath: str = None):
        if not self.index_built:
            raise ValueError('Index is not built yet')

        if not filepath:
            if not self.dest_path:
                raise ValueError('Save Destination Does Not Exist')

            self.annoy_index.save(self.dest_path)
        else:
            self.annoy_index.save(filepath)

    def set_dest_path(self, filepath: str):
        self.dest_path = filepath

    def load_index(self, index_path):
        # check that index path exists

        self.annoy_index.load(index_path)
        self.index_built = True

    def search(self, vector, n_neighbors=10):
        if not self.index_built:
            raise ValueError('Index is not built yet')

        return self.annoy_index.get_nns_by_vector(vector, n_neighbors, include_distances=True)

    def delete(self):
        self.index_built = False
        self.annoy_index = AnnoyIndex(self.vector_size, self.metric)

    def __len__(self):
        return self.annoy_index.get_n_items()

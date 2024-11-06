# from vector_db import VectorDB
import os
import sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)


from Annoy.vector_db import VectorDB  # noqa


def main():
    db = VectorDB(
        dest_path="tests/test_db.db",
        vector_size=3
    )

    vectors = [
        [0, 0, 0],
        [1, 1, 1],
        [1, 0, 0]
    ]

    for id, vec in enumerate(vectors):
        db.add_vector(
            vector_id=id,
            vector=vec
        )

    db.build_index()

    result = db.search(
        vector=[1, 0, 1],
        n_neighbors=3
    )

    print(result)

    for id in result[0]:
        print(vectors[id])

    db.save_index()


if __name__ == "__main__":
    main()

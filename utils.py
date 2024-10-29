import pydantic
import numpy as np


class Entry(pydantic.BaseModel):
    id: int
    vector: np.ndarray


class Search(pydantic.BaseModel):
    vector: np.ndarray
    n: int

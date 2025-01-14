import pydantic

class AddVectorRequest(pydantic.BaseModel):
    vector: list[float]
    vector_id: int
    
class SearchRequest(pydantic.BaseModel):
    query: list[float]
    k: int
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()


# @app.post("/items/")
# async def add_item(vector_request: VectorRequest):

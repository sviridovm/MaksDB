from fastapi import FastAPI
from utils import Entry, Search
from db_manager import ModalDBManager, DBManager

app = FastAPI()

db_mananger = ModalDBManager()


@app.post("/query")
def query(search: Search):
    pass


@app.post("/upsert")
def upsert(entry: Entry):
    pass

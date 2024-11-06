from fastapi import FastAPI
from Annoy.utils import Entry, Search
from Annoy.db_manager import ModalDBManager, DBManager

app = FastAPI()

db_mananger = ModalDBManager()


@app.post("/query")
def query(search: Search):
    pass


@app.post("/upsert")
def upsert(entry: Entry):
    pass

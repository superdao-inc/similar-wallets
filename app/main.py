import os
import sys
import time # noqa
import pandas as pd
from annoy import AnnoyIndex
from fastapi import FastAPI, HTTPException

from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.decl_api import DeclarativeMeta

u = None

current_dir = os.path.dirname(os.path.realpath(__file__))

def log(*args):
    print(*args)
    sys.stdout.flush()

log(f"Current dir: {current_dir}")

db_path = f"{current_dir}/app.db"
index_path = f"{current_dir}/similar_wallets.ann"
map_csv_path = f"{current_dir}/map.csv"

if os.path.exists(db_path):
    os.remove(db_path)

log(f"DB path: {db_path}")
log(f"Index path: {index_path}")

# display all files in current directory
log(f"Files in current directory: {os.listdir(current_dir)}")

# display all files in app directory
log(f"Files in app directory: {os.listdir(current_dir)}")

engine = create_engine(f"sqlite:///{db_path}", poolclass=QueuePool)
with engine.connect() as connection:
    connection.execute(text("PRAGMA journal_mode = OFF;"))
    connection.execute(text("PRAGMA synchronous = 0;"))
    connection.execute(text("PRAGMA cache_size = 2000000;"))
    connection.execute(text("PRAGMA locking_mode = EXCLUSIVE;"))
    connection.execute(text("PRAGMA temp_store = MEMORY;"))

    connection.commit()
    connection.close()

log(f"Engine created: {engine}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
log(f"SessionLocal created: {SessionLocal}")

Base: DeclarativeMeta = declarative_base()
log(f"Base created: {Base}")

class WalletIndex(Base):
    __tablename__ = "wallet_index"
    wallet_index = Column(Integer, primary_key=True)
    wallet_address = Column(String)

def load_data_to_sqlite():
    log("Loading data into SQLite")
    start = time.time()

    prev_time = start
    for chunk in pd.read_csv(map_csv_path, chunksize=1_000_000):
        chunk.to_sql("wallet_index", engine, if_exists="append", index=False)
        log(f"Time to load 1M rows into SQLite: {time.time() - prev_time}")
        prev_time = time.time()

    end = time.time()
    log(f"Time to load data into SQLite: {end - start}")

    session = SessionLocal()  # Create a single session

    # create indexes:
    session.execute(text("CREATE INDEX wallet_index_index ON wallet_index (wallet_index)"))
    session.execute(text("CREATE INDEX wallet_address_index ON wallet_index (wallet_address)"))

    # Close the session when done
    session.close()

    log("Loaded data into SQLite")


def load_annoy_index():
    global u
    u = AnnoyIndex(5, "euclidean")
    u.load(index_path, prefault=False)

    log("Loaded Annoy index")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    log("Starting up")

    Base.metadata.create_all(bind=engine)
    load_data_to_sqlite()
    load_annoy_index()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/annoy/{wallet_address}")
async def read_item(wallet_address: str, n: int = 5):
    with SessionLocal() as session:
        row = (
            session.query(WalletIndex)
            .filter(WalletIndex.wallet_address == wallet_address)
            .first()
        )

    if row is None:
        raise HTTPException(status_code=204)

    vector = u.get_item_vector(row.wallet_index)
    neighbor_indices = u.get_nns_by_vector(vector, n)

    with SessionLocal() as session:
        result = (
            session.query(WalletIndex)
            .filter(WalletIndex.wallet_index.in_(neighbor_indices))
            .all()
        )
        neighbor_addresses = [row.wallet_address for row in result]

    return {"neighbors": neighbor_addresses}
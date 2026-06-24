import pytest

from pyledger.config import MongoSettings
from pyledger.infrastructure.mongo import connect, disconnect


@pytest.fixture(scope="session")
async def mongo_connection(mongo: MongoSettings):
    connection = await connect(mongo)
    yield connection
    await disconnect(connection)


@pytest.fixture
async def clean_db(mongo_connection):
    db = mongo_connection.db
    for name in await db.list_collection_names():
        await db.drop_collection(name)
    yield db

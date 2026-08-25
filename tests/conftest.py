import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database.db as db

_fd, _TEST_DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(_fd)
db.DB_PATH = _TEST_DB_PATH

import app as app_module  # noqa: E402 — must follow the DB_PATH patch


@pytest.fixture
def app():
    app_module.app.config.update(TESTING=True)
    yield app_module.app


@pytest.fixture
def demo_user_id():
    return 1  # seeded once by seed_db(): Demo User / demo@spendly.com


@pytest.fixture
def authenticated_client(client, demo_user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = demo_user_id
    return client

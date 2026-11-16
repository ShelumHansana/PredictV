import os
import sys
import tempfile
from pathlib import Path

# every test run gets its own empty database
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.mkdtemp()).as_posix()}/test.db"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def other_client():
    """A second browser (separate cookie jar)."""
    with TestClient(app) as c:
        yield c

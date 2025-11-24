import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_TMP = Path(tempfile.mkdtemp(prefix="wol-service-tests-"))
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ADMIN_USERNAME", "test_admin")
os.environ.setdefault("ADMIN_PASSWORD", "test_password")
os.environ.setdefault("WOL_HOSTS_PATH", str(_TMP / "hosts.json"))
os.environ.setdefault("USERS_PATH", str(_TMP / "users.json"))
os.environ.setdefault("COOKIE_SECURE", "false")


def pytest_unconfigure(config):
    shutil.rmtree(_TMP, ignore_errors=True)

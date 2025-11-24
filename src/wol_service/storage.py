# src/storage.py
import json, os, tempfile
from typing import List, TypedDict

class Host(TypedDict):
    name: str         # "Gaming PC"
    mac: str          # "AA:BB:CC:DD:EE:FF"
    ip: str           # "192.168.1.23" (or broadcast like "192.168.1.255")
    port: int         # usually 9

DEFAULTS = [
    # intentionally empty to avoid shipping live-looking host data
]

def _atomic_write(path: str, data: str) -> None:
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)  # atomic rename on POSIX

def load_hosts(path: str) -> List[Host]:
    if not os.path.exists(path):
        return DEFAULTS.copy()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_hosts(path: str, hosts: List[Host]) -> None:
    txt = json.dumps(hosts, indent=2, ensure_ascii=False)
    _atomic_write(path, txt)

def ensure_parent_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

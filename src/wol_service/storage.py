# src/storage.py
import json
import os
from typing import List
from wol_service.models import Host
from wol_service.utils import atomic_write


def load_hosts(path: str) -> List[Host]:
    if not os.path.exists(path):
        return list()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_hosts(path: str, hosts: List[Host]) -> None:
    atomic_write(path, hosts)

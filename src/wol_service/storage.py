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
        data = json.load(f)
    if isinstance(data, list):
        return [
            Host(name=item["name"], mac=item["mac"], ip=item["ip"], port=item["port"])
            for item in data
        ]
    return []


def save_hosts(path: str, hosts: List[Host]) -> None:
    atomic_write(path, [dict(h) for h in hosts])

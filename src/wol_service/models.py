from typing import TypedDict


class Host(TypedDict):
    name: str  # "Gaming PC"
    mac: str  # "AA:BB:CC:DD:EE:FF"
    ip: str  # "192.168.1.23" (or broadcast like "192.168.1.255")
    port: int  # usually 9


class User(TypedDict):
    username: str
    hashed_password: str

import json
import os
import tempfile
from pathlib import Path
import importlib.util


def get_resource_path(package_name: str, resource_name: str) -> Path:
    """
    Get the path to a resource directory within a package.
    This works for both development (editable install) and packaged installations.
    """
    spec = importlib.util.find_spec(package_name)
    if not spec or not spec.origin:
        raise ImportError(f"Could not find the spec for package '{package_name}'")
    package_dir = Path(spec.origin).parent
    return package_dir / resource_name


def ensure_parent_dir(path: str | Path) -> None:
    """Ensures the parent directory of a file path exists."""
    parent_dir = Path(path).parent
    if parent_dir:
        parent_dir.mkdir(parents=True, exist_ok=True)


def atomic_write(path: str | Path, data: str | dict | list) -> None:
    """Atomically writes data to a file."""
    ensure_parent_dir(path)
    path = Path(path)
    d = path.parent if path.parent != Path("") else Path(".")
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=path.suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

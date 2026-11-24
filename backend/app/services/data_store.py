"""In-memory cache over processed CSV files on disk.

Processed data lives under data/processed/*.csv. The store lazily loads and
caches them so routes do not re-read disk on every request. Call
``reload()`` after a fresh ingestion run.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

import pandas as pd

PROCESSED_DIR = os.path.join("data", "processed")

_CACHE: dict[str, pd.DataFrame] = {}
_LOCK = threading.Lock()


def _path(name: str) -> str:
    return os.path.join(PROCESSED_DIR, name)


def load(name: str) -> pd.DataFrame:
    """Load (and cache) a processed CSV by file name (with or without .csv)."""
    if not name.endswith(".csv"):
        name = name + ".csv"
    with _LOCK:
        if name in _CACHE:
            return _CACHE[name].copy()
        path = _path(name)
        if not os.path.exists(path):
            df = pd.DataFrame()
        else:
            try:
                df = pd.read_csv(path)
            except Exception:
                df = pd.DataFrame()
        _CACHE[name] = df
        return df.copy()


def save(name: str, df: pd.DataFrame) -> str:
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    if not name.endswith(".csv"):
        name = name + ".csv"
    path = _path(name)
    df.to_csv(path, index=False)
    with _LOCK:
        _CACHE[name] = df.copy()
    return path


def reload() -> None:
    with _LOCK:
        _CACHE.clear()


def available() -> list[str]:
    if not os.path.isdir(PROCESSED_DIR):
        return []
    return sorted(f for f in os.listdir(PROCESSED_DIR) if f.endswith(".csv"))
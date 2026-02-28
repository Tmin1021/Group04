from __future__ import annotations

import os
from pathlib import Path
import yaml
import logging

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "config.yaml"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

# Data dir (can be overridden with DATA_DIR env var)
DATA_DIR = Path(os.environ.get("DATA_DIR", config["data"]["data_dir"]))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Simple logger
logger = logging.getLogger("qvm")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

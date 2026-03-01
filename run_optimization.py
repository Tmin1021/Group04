from __future__ import annotations

from src.settings import config, logger
from src.optimize.optimize_momentum import optimize_momentum


def main() -> None:
    logger.info("Running optimization on in-sample period")
    out = optimize_momentum(config)
    logger.info("Best config found: %s", out["best"])


if __name__ == "__main__":
    main()

"""Application-wide logging configuration."""

import logging
from sys import stdout


def config_logging(level: str, filename: str, filemode: str) -> None:
    """Configure root logger with file and stdout handlers.

    Args:
        level: Log level name (e.g. "DEBUG", "INFO").
        filename: Path to the log file.
        filemode: File open mode ("w" to overwrite, "a" to append).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(filename, mode=filemode),
            logging.StreamHandler(stdout),
        ],
    )

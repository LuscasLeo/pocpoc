import logging
from pathlib import Path
from fnmatch import fnmatch
from typing import Generator, List
from pocpoc.api.context_tracker.conte_logging_addon import (
    ContextTrackerLoggingAddon,
)
from pocpoc.api.logging.json_logging_formatter import (
    JsonLoggingFormatter,
)


import colorlog


def configure_logs(
    *patterns: str,
    exclude_types: List[str] = [],
) -> Generator[logging.Logger, None, None]:
    for name, logger in logging.getLogger().manager.loggerDict.items():  # type: ignore
        if not isinstance(logger, logging.Logger):
            continue

        if any(
            fnmatch(name, module_pattern) for module_pattern in exclude_types
        ) or not any(fnmatch(name, module_pattern) for module_pattern in patterns):
            continue

        yield logger


def setup_debug_logging(*module_patterns: str) -> None:
    json_formatter = JsonLoggingFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(process)d - %(thread)d - %(threadName)s",
    )

    json_formatter.add_addon(ContextTrackerLoggingAddon())

    # logging.getLogger().setLevel(logging.WARNING)

    Path("temp").mkdir(exist_ok=True)

    for logger in configure_logs(*module_patterns):
        file_handler = logging.FileHandler("temp/test.log")
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)

        stream_handler = colorlog.StreamHandler()
        stream_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s %(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
                secondary_log_colors={},
                style="%",
            )
        )
        logger.addHandler(stream_handler)

        logger.setLevel(logging.DEBUG)
        # logging.getLogger("__main__").setLevel(logging.DEBUG)

        logger.debug("Logging initialized")


def set_production_logging(*module_patterns: str) -> None:
    json_formatter = JsonLoggingFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(process)d - %(thread)d - %(threadName)s",
    )

    json_formatter.add_addon(ContextTrackerLoggingAddon())

    Path("temp").mkdir(exist_ok=True)

    for logger in configure_logs(*module_patterns):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(json_formatter)
        logger.addHandler(stream_handler)

        logger.setLevel(logging.DEBUG)
        # logging.getLogger("__main__").setLevel(logging.DEBUG)

        logger.debug("Logging initialized")

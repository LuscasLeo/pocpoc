import importlib
import logging
import os
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
import sys
from time import sleep
from typing import List

import click

from pocpoc.api.microservices import ContainerHandler, GracefulKiller

logger = logging.getLogger(__name__)


def get_command_handler_from_module_path(full_path: str) -> ContainerHandler:
    module_path, class_name = full_path.rsplit(":", 1)

    module = importlib.import_module(module_path)
    handler = getattr(module, class_name)

    if not isinstance(handler, ContainerHandler):
        raise ValueError(f"Handler {handler} is not a ContainerHandler. ")

    return handler


def bootstrap(handler_path: str, index: int) -> None:
    logger.info("Starting worker %s on process %s", index, os.getpid())

    handler = get_command_handler_from_module_path(handler_path)

    handler.run()


def bootstrap_multiprocess(handler_path: str, pool_size: int) -> None:
    GracefulKiller.setup()

    logger.info("Starting Pool. PID: %s", os.getpid())

    with ProcessPoolExecutor(max_workers=pool_size) as pool:
        futures = [pool.submit(bootstrap, handler_path, i) for i in range(pool_size)]

        while True:
            new_list: List["Future[None]"] = []
            for future in as_completed([*futures]):
                try:
                    future.result()
                except Exception as e:
                    logger.critical("Exception in worker: %s", e, exc_info=True)

                if not GracefulKiller.should_continue():
                    logger.info("GracefulKiller received signal. Exiting.")
                    pool.shutdown(wait=True)
                    sys.exit(2)
                    return
                sleep(4)
                new_list.append(pool.submit(bootstrap, handler_path, len(new_list)))

            futures = new_list


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--workers", "-w", default=1, type=int)  # type: ignore
@click.argument("handler")  # type: ignore
def run(workers: int, handler: str) -> None:
    get_command_handler_from_module_path(handler)

    bootstrap_multiprocess(handler, workers)


if __name__ == "__main__":
    cli()

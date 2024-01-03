"""Logging utilities for Pandarus."""
import datetime
import logging
import os
from logging.handlers import QueueListener
from multiprocessing import Queue
from typing import Optional, Tuple


def logger_init(log_dir: Optional[str] = None) -> Tuple[QueueListener, Queue]:
    """Initialize a logger. Adapted from
    http://stackoverflow.com/a/34964369/164864."""
    log_path = (
        f"pandarus-worker-{datetime.datetime.now().strftime('%d-%B-%Y-%I-%M%p')}.log"
    )
    if log_dir is not None:
        log_path = os.path.join(log_dir, log_path)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(lineno)d %(message)s")
    )

    # queue_listener gets records from the queue and sends them to the handler
    logging_queue = Queue()
    queue_listener = QueueListener(logging_queue, handler)
    queue_listener.start()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return queue_listener, logging_queue

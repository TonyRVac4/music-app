import logging
import os
import sys
from os import path
from logging.handlers import TimedRotatingFileHandler

if not path.exists("logs/"):
    os.mkdir("logs/")


def configure_logger() -> None:
    logger = logging.getLogger("my_app")
    formatter = logging.Formatter(fmt=
                                  "%(asctime)s - [%(levelname)s] - %(filename)s.%(funcName)s(%(lineno)d) - %(message)s"
                                  )

    # stream_handler = logging.StreamHandler(stream=sys.stdout)
    file_handler = TimedRotatingFileHandler(
        filename="logs/app.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    error_file_handler = TimedRotatingFileHandler(
        filename="logs/error.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    warning_file_handler = TimedRotatingFileHandler(
        filename="logs/warning.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )

    # stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)
    warning_file_handler.setFormatter(formatter)

    file_handler.setLevel("DEBUG")
    error_file_handler.setLevel("ERROR")
    warning_file_handler.setLevel("WARNING")

    # add stream_handler
    logger.handlers = [file_handler, error_file_handler, warning_file_handler]
    logger.propagate = False
    logger.setLevel("DEBUG")

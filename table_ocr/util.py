from contextlib import contextmanager
import functools
import logging
import os
import tempfile

def get_logger(name):
    logger = logging.getLogger(name)
    lvl = os.environ.get("PY_LOG_LVL", "info").upper()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    handler.setLevel(lvl)
    logger.setLevel(lvl)
    return logger

@contextmanager
def working_dir(directory):
    original_working_dir = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(original_working_dir)


def make_tempdir(identifier):
    return tempfile.mkdtemp(prefix="{}_".format(identifier))

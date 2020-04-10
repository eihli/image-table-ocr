from contextlib import contextmanager
import functools
import logging
import os
import tempfile

from bs4 import BeautifulSoup as bs
import requests




logger = get_logger()




@contextmanager
def working_dir(directory):
    original_working_dir = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(original_working_dir)


def download(url, filepath):
    response = request_get(url)
    data = response.content
    with open(filepath, "wb") as f:
        f.write(data)


def make_tempdir(identifier):
    return tempfile.mkdtemp(prefix="{}_".format(identifier))

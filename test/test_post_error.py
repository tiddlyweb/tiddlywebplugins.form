"""
tests to ensure that the appropriate error codes are sent back when something
goes wrong
"""

from setup_test import setup_store, setup_web
from tiddlywebplugins.form import get_form

from tiddlyweb.config import config
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.bag import Bag
from tiddlyweb.store import NoTiddlerError

import httplib2
import cgi

config['system_plugins'] = ['tiddlywebplugins.form']

def test_bad_input_error():
    """
    if the form cannot be read, then a 400 should be returned
    """
    store = setup_store()
    setup_web()
    http = httplib2.Http()

    response = http.request('http://test_domain:8001/bags/foo/tiddlers',
        method='POST',
        headers={'Content-type': 'multipart/form-data'},
        body='title=HelloWorld&text=Hi%20There')[0]

    assert response['status'] == '400'

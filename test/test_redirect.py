"""
tests to ensure that the optional redirect works properly
"""

from setup_test import setup_store, setup_web

from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.config import config

import httplib2

config['system_plugins'] = ['tiddlywebplugins.form']

def test_post_redirect():
    """
    add a tiddler, specifying a url to redirect to on success
    """
    store = setup_store()
    setup_web()
    http = httplib2.Http()

    #add a tiddler specifying a redirect
    http.follow_redirects = False
    response = http.request('http://test_domain:8001/recipes/foobar/tiddlers' \
        '?redirect=/bags/foo/tiddlers',
        method='POST', 
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        body='title=HelloWorld&text=Hi%20There')[0]
    
    #make sure the redirect has been applied
    assert response.status == 303
    assert response['location'].split('?')[0] == '/bags/foo/tiddlers'
    
    #check the tiddler was saved
    #now check the tiddler tags
    tiddler = Tiddler('HelloWorld', 'bar')
    try:
        store.get(tiddler)
    except NoTiddlerError:
        raise AssertionError('tiddler was not put into store')
    
    assert tiddler.title == 'HelloWorld'
    assert tiddler.text == 'Hi There'
    assert tiddler.fields.get('redirect', None) == None

def test_post_redirect_in_body():
    """
    add a tiddler, specifying a url to redirect to in the body of the post
    """
    store = setup_store()
    setup_web()
    http = httplib2.Http()

    #add a tiddler specifying a redirect
    http.follow_redirects = False
    response = http.request('http://test_domain:8001/recipes/foobar/tiddlers',
        method='POST', 
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        body='title=HelloWorld&text=Hi%20There&redirect=/bags/foo/tiddlers')[0]

    #make sure the redirect has been applied
    assert response.status == 303
    assert response['location'].split('?')[0] == '/bags/foo/tiddlers'

    #check the tiddler was saved
    tiddler = Tiddler('HelloWorld', 'bar')
    tiddler = store.get(tiddler)

    assert tiddler.title == 'HelloWorld'
    assert tiddler.text == 'Hi There'
    assert tiddler.fields.get('redirect', None) == None
"""
Provides a Serializer to transform HTML form-data into an object that can be
put into the store.

Also adds POST support to the standard set of URLs

NOTE - A large proportion of this code will disappear when TiddlyWeb 1.1 is released.
This is due to improved handling in TiddlyWeb that allows items to be put into the store
from any content type as long as their is a serialization for it. Pre 1.1 TiddlyWeb
requires the content type to be text/plain or application/json only, hence most of this
code is just a replication of TiddlyWeb core with subtle changes to it.
"""
import logging
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.web.handler.tiddler import put
from tiddlyweb.serializer import Serializer, TiddlerFormatError
from tiddlyweb.serializations import SerializationInterface 
from tiddlyweb.web import util as web
from cgi import FieldStorage
from socket import timeout
import re
import urllib
from uuid import uuid4
from StringIO import StringIO


def get_form(environ):
    form = {
        'application/x-www-form-urlencoded': environ['tiddlyweb.query'],
        'multipart/form-data': FieldStorage(fp=environ['wsgi.input'], environ=environ)
    }
        
    return form.get(environ['tiddlyweb.type'])
    
def retrieve_item(obj, key): 
    if getattr(obj, 'getfirst', None):
        return obj.getfirst(key)
    else:
        return obj[key][0]

def post_tiddler_to_container(environ, start_response):
    """
    entry point for recipes/foo/tiddlers or bags/foo/tiddlers

    we have included the tiddler name in the form,
    so get that and carry on as normal
    """
    try:
        form = get_form(environ)
    except timeout:
        return []

    def get_name():
        if 'title' in form:
            return retrieve_item(form, 'title')
        else:
            return form['file'].filename

    try:
        tiddler_name = urllib.quote(get_name())
    except KeyError:
        tiddler_name = str(uuid4())
    
    Serialization.form = form
    try:
        redirect = environ['tiddlyweb.query'].pop('redirect')
        if '?' in redirect[0] and not redirect[0].endswith('?'):
            redirect[0] += '&'
        else:
            redirect[0] += '?'
        redirect[0] += '.no-cache=%s' % uuid4()
    except KeyError:
        redirect = None

    #mock up some objects that tiddlyweb.web.handler.tiddler.put requires
    environ['wsgiorg.routing_args'][1]['tiddler_name'] = tiddler_name
    environ['REQUEST_METHOD'] = 'PUT'
    environ['wsgi.input'] = StringIO('dummy input')
    def dummy_start_response(response_code, *args):
        """
        start_response may only be called once.
        We may need it to be a redirect instead of a 204
        """
        if not response_code.startswith('204'):
            start_response(response_code, *args)
        elif redirect:
            response = [('Location', str(redirect[0]))]
            start_response('303 See Other', response)
        else:
            start_response(response_code, *args)

    return put(environ, dummy_start_response)

class Serialization(SerializationInterface):
    def as_tiddler(self, tiddler, input_string=None):
        """
        turn a form input into a tiddler
        nb: input_string is ignored. You need to set Serialization.form
        to the form object prior to calling.
        """
        if 'file' in self.form and getattr(self.form['file'], 'file', None): 
            my_file = self.form['file']
            if not my_file.file: raise TiddlerFormatError
            tiddler.type = my_file.type
            tiddler.text = my_file.file.read()
            if 'tags' in self.form:
                if getattr(self.form, 'getfirst', None):
                    tags = self.form.getlist('tags')
                else:
                    tags = self.form['tags']
                tiddler.tags = []
                for tag in tags:
                    tiddler.tags.extend(self.create_tag_list(tag))
        else:
            keys = ['created', 'modified', 'modifier', 'text']
            for key in self.form:
                if key in keys:
                    setattr(tiddler, key, retrieve_item(self.form, key))
                elif key == 'tags':
                    if getattr(self.form, 'getfirst', None):
                        tags = self.form.getlist(key)
                    else:
                        tags = self.form[key]
                    tiddler.tags = []
                    for tag in tags:
                        tiddler.tags.extend(self.create_tag_list(tag))
                else:
                    tiddler.fields[key] = retrieve_item(self.form, key)              
        
        return tiddler
    
    def create_tag_list(self, input_string):
        regex = '\[\[([^\]\]]+)\]\]|(\S+)'
        matches = re.findall(regex, input_string)
        tags = set()
        for bracketed, unbracketed in matches:
            tag = bracketed or unbracketed
            tags.add(tag)
        return list(tags)

def update_handler(selector, path, new_handler, server_prefix):
    """
    Update an existing path handler in the selector
    map with new methods (in this case, POST). 
    
    Taken and modified from tiddlywebplugins
    returns true if match successful
    """
    regexed_path = selector.parser(path)
    regexed_prefixed_path = selector.parser(server_prefix + path)
    for index, (regex, handler) in enumerate(selector.mappings):
        if regexed_path == regex.pattern or regexed_prefixed_path == regex.pattern:
            handler.update(new_handler)
            selector.mappings[index] = (regex, handler)
            return

    logging.debug('%s not found in URL mapping. Not replaced' % path)

def init(config):
    """
    add POST handlers to the standard set of URLs.
    nb - revisions not included as POST already exists
    
    register the serializer for Content-Type: application/x-www-form-urlencoded 
    and Content-Type: multipart/form-data 
    """
    if not 'selector' in config:
        return
    selector = config['selector']
    
    update_handler(selector, '/recipes/{recipe_name:segment}/tiddlers[.{format}]',
        dict(POST=post_tiddler_to_container), config.get('server_prefix', ''))
    update_handler(selector, '/bags/{bag_name:segment}/tiddlers[.{format}]',
        dict(POST=post_tiddler_to_container), config.get('server_prefix', ''))

    config['extension_types']['form'] = 'application/x-www-form-urlencoded'
    config['serializers']['application/x-www-form-urlencoded'] = \
        ['tiddlywebplugins.form', 'application/x-www-form-urlencoded; charset=UTF-8']
    config['serializers']['multipart/form-data'] = \
        ['tiddlywebplugins.form', 'multipart/form-data; charset=UTF-8']

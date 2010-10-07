"""
some initialisation stuff needed for each test
"""

from tiddlyweb.config import config
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.recipe import Recipe
from tiddlyweb.store import NoBagError, NoRecipeError
from tiddlyweb.web import serve

from tiddlywebplugins.utils import get_store

from wsgi_intercept import httplib2_intercept
import wsgi_intercept
import httplib2

BAGS = [
    'foo',
    'bar'
]

RECIPES = {
    'foobar': [('foo', ''), ('bar', '')]
}

def setup_store():
    """
    initialise a blank store, and fill it with some data
    """
    store = get_store(config)

    for bag in store.list_bags():
        store.delete(bag)

    for bag in BAGS:
        bag = Bag(bag)
        store.put(bag)
    
    for recipe in store.list_recipes():
        store.delete(recipe)

    for recipe, contents in RECIPES.iteritems():
        recipe = Recipe(recipe)
        recipe.set_recipe(contents)
        store.put(recipe)
        
    return store
    
def setup_web():
    """
    set up TiddlyWeb to run as a mock server
    This is required to get selector loaded
    """
    def app_fn():
        return serve.load_app()
        
    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('test_domain', 8001, app_fn)

import requests
import copy


class Sheet(object):
    """Thin requests wrapper for RESTful interfaces"""

    def __init__(self, name, parent=None, session=None, **kwargs):
        self._name = name
        self._parent = parent
        self._session = session if session is not None else requests.session()
        for k, v in kwargs.items():
            setattr(self._session, k, v)

    def __getattr__(self, name):
        """All attributes are children nodes"""
        if name.startswith("__"):
            raise AttributeError(name)
        return self._copy(name)

    def __iter__(self):
        """Iterates up the parent chain"""
        node = self
        while node:
            if node._name:
                yield node
            node = node._parent

    def __repr__(self):
        """Curren URL of nodes"""
        return ""

    def _insert(self, *args):
        """Inserts args as child nodes"""
        node = self
        for a in args:
            node = node._copy(str(a))
        return node

    def _copy(self, name):
        """Create shallow copy of self as child node"""
        node = copy.copy(self)
        node._name = name
        node._parent = self
        return node

    def _request(self, method, *args, **kwargs):
        """Make method HTTP request"""
        return self._session.request(method, self._url(*args), **kwargs)

    def _url(self, *args):
        """Converts nodes to URL string"""
        nodes = reversed([n._name for n in self._insert(*args)])
        return "/".join(nodes)


def bind_method(method):
    def sink(self, *args, **kwargs):
        return self._request(method, *args, **kwargs)
    return sink

METHODS = ["GET", "POST", "PATCH", "DELETE"]

for m in METHODS:
    setattr(Sheet, m, bind_method(m))

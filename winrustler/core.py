"""
A module to put things in that I don't care to come up with a better name for
where they belong ...
"""

FIELD_HELP = 'help'
REGISTRY = set()

def register_module():
    """
    Decorator for a class with the class method `add_subparser` used to
    help instantiate the object; but is generally not sufficient, a hwnd must
    be provided to the instance ctor.

    Instances should have a method `run` which is `callable()`.
    """
    def _register_this(cls):
        assert cls not in REGISTRY
        REGISTRY.add(cls)
        return cls
    return _register_this

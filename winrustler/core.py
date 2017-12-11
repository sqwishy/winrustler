"""
"""

FIELD_HELP = 'help'
REGISTRY = set()

def register_module():
    """
        - `parser` of `argparse.ArgumentParser` and a
        - `run` which is `callable(WindowCollection, argparse.Namespace)`
    """
    def _register_this(cls):
        assert cls not in REGISTRY
        REGISTRY.add(cls)
        return cls
    return _register_this

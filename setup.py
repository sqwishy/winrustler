import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "WinRustler",
    version = "0.9.1",  # Keep in sync with winrustler/__init__.py
    author = "somebody",
    author_email = "somebody@froghat.ca",
    description = ("Thing for rustling windows in Windows."),
    license = "GPLv3",
    packages=['winrustler'],
    long_description=read('README.rst'),
    classifiers=[
        "Banana :: Bread",
    ],
    entry_points={
        'console_scripts': [
            'winrustler=winrustler.__main__:main',
            'winrustler-ui=winrustler.ui.__main__:main',
        ],
    },
)

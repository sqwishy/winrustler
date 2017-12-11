import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "winrustler",
    version = "0.0.1",
    author = "somebody",
    author_email = "somebody@froghat.ca",
    description = ("thing for rustling windows in windows"),
    license = "???",
    packages=['winrustler'],
    long_description=read('README'),
    classifiers=[
        "Banana :: Bread",
    ],
    entry_points={
        'console_scripts': [
            'winrustler=winrustler.__main__:main',
        ],
    },
)

import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="WinRustler",
    version="0.11.0",  # Keep in sync with winrustler/__init__.py
    author="sqwishy",
    author_email="somebody@froghat.ca",
    description=("Thing for rustling windows in Windows."),
    license="GPLv3",
    packages=["winrustler", "winrustler.ui", "winrustler.ui.widgets"],
    package_data={
        "": [
            "ui/res/%s" % icon
            for icon in "1f40a.png 1f412.png 1f47b.png 1f49f.png 1f4d0.png 1f5bc.png 1f984.png".split()
        ]
    },
    long_description=read("README.md"),
    classifiers=[
        "Banana :: Bread",
    ],
    install_requires=[
        "attrs==17.*",
        "PyQt5",
    ],
    entry_points={
        "console_scripts": [
            "winrustler=winrustler.__main__:main",
            "winrustler-ui=winrustler.ui.__main__:main",
        ],
    },
)

from setuptools import setup

from os import path
from configparser import ConfigParser
import subprocess

GITMODULES_PATH = ".gitmodules"
config = ConfigParser()
config.read(GITMODULES_PATH)

for section in config.sections():
    if section.startswith("submodule "):
        submodule_info = dict(config.items(section=section))
        submodule_path = submodule_info["path"]
        submodule_url  = submodule_info["url"]

        subprocess.run(["git", "clone", submodule_url, submodule_path])

submodule_setup = subprocess.Popen(["git", "submodule", "update", "--init", "--recursive"], shell=True)
submodule_setup.wait()

import astars

NAME = 'astars'
DESCRIPTION = "astars: An unified programming language parser & analyse AST tool for Souece Code Analysis.  "

AUTHOR = 'Wakana Hashimoto'
AUTHOR_EMAIL = 'oxwasouxo@gmail.com'
URL = 'https://github.com/xwasoux'

LICENSE = 'MIT'
DOWNLOAD_URL = 'https://github.com/xwasoux/astars.git'
PYTHON_REQUIRES = ">=3.8"

INSTALL_REQUIRES = [
    'anytree',
    'graphviz',
    'pydot',
    'tree_sitter',
]

PACKAGES = [
    'astars'
]

CLASSIFIERS = [
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3 :: Only',
    'Topic :: Scientific/Engineering',
    'Topic :: Scientific/Engineering :: Visualization',
    'Topic :: Scientific/Engineering :: Artificial Intelligence',
]

PACKAGE_DATA = { 
    "tree-sitter": [path.join("astars", "parser" "grammar", "tree-sitter", "*")] 
}

setup(
    name=NAME,
    description=DESCRIPTION,
    license=LICENSE,

    url=URL,
    download_url=DOWNLOAD_URL,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,

    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,

    packages=PACKAGES,
    package_data=PACKAGE_DATA, 
    classifiers=CLASSIFIERS
    )

from setuptools import setup

NAME = 'astars'
DESCRIPTION = "Astars: AST analysis and manipulation tools for diverse languages."

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

USE_SCM_VERSION = True
SETUP_REQUIRES = [
    "setuptools>=42",
    "setuptools_scm>=3.4",
]

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
    classifiers=CLASSIFIERS,
    use_scm_version=USE_SCM_VERSION,
    setup_requires=SETUP_REQUIRES,
    )

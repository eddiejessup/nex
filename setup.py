from setuptools import setup, find_packages
# To use a consistent encoding.
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='nex',

    version='0.1.0',

    description='Tickle document preparation with technology',
    long_description=long_description,

    url='https://github.com/eddiejessup/nex',

    author='Elliot Marsden',
    author_email='elliot.marsden@gmail.com',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Documentation',
        'Topic :: Printing',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Text Editors :: Word Processors',
        'Topic :: Text Processing :: Markup :: LaTeX',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.6',
    ],

    # What does your project relate to?
    keywords='latex text pdf typesetting',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['docs', 'tests']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'colorama>=0.3.9,<1',
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': [],
        'test': [
            'coverage',
            'pytest',
            'pytest-cov',
        ],
    },

    # Data files included in package that need to be installed.
    package_data={},

    # Although 'package_data' is preferred, sometimes you may need to place
    # data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    entry_points={
        'console_scripts': [
            'nex=nex.nex:main',
        ],
    },
)

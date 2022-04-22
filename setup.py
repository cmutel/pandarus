from setuptools import setup
import os

requirements = [
    "appdirs",
    "fiona",
    "numpy",
    "pyproj",
    "Rtree",
    "rasterio",
    "rasterstats",
    "shapely",
]

setup(
    version="1.1",
    author="Chris Mutel",
    author_email="cmutel@gmail.com",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
    package_data={'pandarus': [
        "tests/data/*.*",
    ]},
    install_requires=[] if os.environ.get('READTHEDOCS') else requirements,
    license=open('LICENSE', encoding='utf-8').read(),
    long_description=open('README.md', encoding='utf-8').read(),
    name='pandarus',
    packages=["pandarus"],
    url="https://github.com/cmutel/pandarus",
)

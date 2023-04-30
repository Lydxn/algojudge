from setuptools import find_packages, setup
from Cython.Build import cythonize


setup(
    name='algojudge',
    version='0.0.0',
    packages=find_packages(),
    ext_modules=cythonize('algojudge/comparators/_compare.pyx')
)

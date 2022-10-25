from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='optas',
    version='1.0.0',
    description='OpTaS: An optimization-based task specification library for task and motion planning (TAMP), trajectory optimization, and model predictive control.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/cmower/optas',
    project_urls={
        "Bug Tracker": "https://github.com/cmower/optas/issues",
    },
    author='Christopher E. Mower',
    author_email='christopher.mower@kcl.ac.uk',
    license='BSD 2-Clause License',
    packages=['optas'],
    test_suite='test',
    install_requires=[
        'numpy',
        'scipy',
        'casadi',
        'urdf-parser-py',
        'osqp',
        'cvxopt',
        'pybullet',
    ]
)

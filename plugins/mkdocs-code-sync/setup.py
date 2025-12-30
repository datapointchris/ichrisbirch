from setuptools import find_packages
from setuptools import setup

setup(
    name='mkdocs-code-sync',
    version='0.1.0',
    description='MkDocs plugin for synchronizing code snippets with the actual codebase',
    author='Chris Birch',
    author_email='your-email@example.com',
    packages=find_packages(),
    install_requires=[
        'mkdocs>=1.1.0',
    ],
    entry_points={
        'mkdocs.plugins': [
            'code_sync = mkdocs_code_sync:entry_point',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)

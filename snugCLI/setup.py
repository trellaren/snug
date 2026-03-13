from importlib.metadata import entry_points

from setuptools import setup, find_packages

setup(
    name="snugCLI",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'GPUtils',
        'wmi',
        'psutil',
        'platform',
        'setuptools'
    ],
    entry_points={
        'console_scripts': [
            'snug = main:hello',
        ]
    }
)
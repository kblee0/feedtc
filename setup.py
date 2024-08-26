from setuptools import setup, find_packages

setup(
    name='feedtc',
    version='0.1.0',
    packages=find_packages(include=['feedtc']),
    package_data={},
    install_requires=[
        'PyVirtualDisplay',
        'pyyml',
        'requests',
        'selenium',
        'transmissionrpc',
        'urllib3'
    ],
    entry_points={
        'console_scripts': ['feedtc=feedtc.__main__']
    },
    windows = [
        {
            'icon_resources': [(1, "cm/cm.ico")],
            'console':False
        }
    ]
)

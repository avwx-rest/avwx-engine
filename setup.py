from setuptools import setup
from babel.messages import frontend as babel

setup(
    name='avwx-engine',
    version='0.9',
    description='Aviation weather report parsing library',
    url='https://github.com/flyinactor91/AVWX-Engine',
    author='Michael duPont',
    author_email='michael@mdupont.com',
    packages=[
        'avwx'
    ],
    package_data={
        'avwx': [
            'stations.sqlite'
        ]
    },
    cmdclass={
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    }
)

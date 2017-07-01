from setuptools import setup
from babel.messages import frontend as babel

setup(
    name='avwx-engine',
    version='0.9.1',
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
        'compile': babel.compile_catalog,
        'extract': babel.extract_messages,
        'init': babel.init_catalog,
        'update': babel.update_catalog
    }
)

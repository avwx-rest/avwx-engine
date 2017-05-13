from setuptools import setup

setup(name='avwx-engine',
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
      }
)
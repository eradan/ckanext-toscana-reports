from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-toscana_reports',
    version=version,
    description="Custom Reports for Dati Toscana",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Ivan Ricotti',
    author_email='i.ricotti@hyperborea.com',
    url='http://www.hyperborea.com',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.toscana_reports'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
	datitoscana_reports=ckanext.toscana_reports.plugin:DatiToscanaReportsPlugin
        # Add plugins here, e.g.
        # myplugin=ckanext.toscana_reports.plugin:PluginClass
    ''',
)

import os

from setuptools import find_packages, setup

from blueprints import __version__

# read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="aa-blueprints",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    license="GPL",
    description="Blueprint Library plugin for Alliance Auth",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rebecca Murphy",
    author_email="rebecca@rcmurphy.me",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.1",
        "Intended Audience :: Developers",
        # example license
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)

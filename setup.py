from setuptools import setup

setup(
    name="p2a_impacts",
    version="0.0.1",
    description="Climate impacts engine for Plan2Adapt.ca",
    url="https://pland2adapt.ca",
    author="Nikola Rados",
    author_email="nrados@uvic.ca",
    install_requires=["ce>=1.1", "GDAL==2.2", "numpy>=1.16", "requests", "sly"],
    license="GPLv3",
    packages=["p2a_impacts"],
    zip_safe=True,
    scripts=["scripts/process.py"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
)

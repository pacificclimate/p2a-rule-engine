from setuptools import setup

__version__ = (0, 4, 0)

setup(
    name="p2a_impacts",
    version=".".join(str(d) for d in __version__),
    description="Climate impacts engine for Plan2Adapt.ca",
    url="https://pland2adapt.ca",
    author="Nikola Rados",
    author_email="nrados@uvic.ca",
    install_requires=["ce", "contexttimer", "GDAL", "numpy", "requests", "sly",],
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

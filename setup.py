"""Python setup.py for lifelog package"""
import io
from setuptools import find_packages, setup

# Load the long description from README.md
with io.open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="Lifelog",
    version="1.0.0",
    description="A simple and secure diary app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MrBeam89/lifelog/",
    download_url="https://pypi.org/project/Lifelog/",
    license="GPLv3",
    author="MrBeam89_",
    author_email='mrbeam89@protonmail.com',
    maintainer="MrBeam89_",
    maintainer_email='mrbeam89@protonmail.com',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Office/Business :: News/Diary",
    ],
    install_requires=[
        "pygobject",
        "scrypt",
        "pycryptodomex"
    ],
    entry_points={
        "console_scripts": ["lifelog = lifelog.__main__:run"]
    },
    include_package_data=True,
    package_data = {
        'lifelog': [
            'res/ui.glade',
            'res/icon_128.png'
        ]
    },
    extras_require={
        "dev": ["twine"]
    },
    python_requires=">=3.9",
)

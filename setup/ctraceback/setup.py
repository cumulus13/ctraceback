import io
from setuptools import setup, find_packages
import sys

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

version = {}
with open("__version__.py") as fp:
    exec(fp.read(), version)
version = version['version']

if sys.platform == 'win32':
    install_requires = [
        'pygetwindow',
        'argparse',
        'configset', 
        'rich',
        'pydebugger',
        'ctype',
        'pywin32',  
        'psutil'
    ]
else:
    install_requires = [
        'argparse',
        'configset', 
        'rich',
        'pydebugger',
    ]

setup(
    name="ctraceback",
    version=version,
    url="https://github.com/cumulus13/ctraceback",
    project_urls={
        "Documentation": "https://github.com/cumulus13/ctraceback",
        "Code": "https://github.com/cumulus13/ctraceback",
    },
    license="GPL",
    author="Hadi Cahyadi LD",
    author_email="cumulus13@gmail.com",
    maintainer="cumulus13 Team",
    maintainer_email="cumulus13@gmail.com",
    description="Custom traceback",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "ctraceback = ctraceback.__main__:usage",
        ]
    },
    data_files=['__version__.py', 'README.md', 'LICENSE.rst'],
    license_files=["LICENSE.rst"],    
    include_package_data=True,
    python_requires=">=3",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: GNU General Public License (GPL)', 
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)

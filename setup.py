import setuptools


# Get the long description from the README
with open('README.md', 'r') as file:
    long_description = file.read()


# Use setuptools.setup to configure our package for PYPI
setuptools.setup(

    name='google-drive-cli',
    version='0.0.3',

    author='Mark Allamanno',
    author_email='mark.allamanno@gmail.com',
    url='https://github.com/mark-allamanno/google-drive-cli',

    description='A Google Drive CLI Client',
    long_description=long_description,
    long_description_content_type='text/markdown',

    package_dir={'': 'google-drive-cli'},
    py_modules=['cloud', 'commands', 'exceptions', 'main'],

    install_requires=['prompt-toolkit', 'pydrive2', 'fuzzywuzzy', 'python-Levenshtein'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],

    python_requires='>=3.8'
)

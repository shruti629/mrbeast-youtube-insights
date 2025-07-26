from setuptools import setup, find_packages
from typing import List

HYPEN_E_DOT = '-e .'    

def get_requirements(file_path) -> List[str]:
    '''This function will return the list of requirements from the given file path.'''

    requirements = []

    with open (file_path) as file_obj:
        requirements = file_obj.readlines()
        requirements = [req.replace('\n', '') for req in requirements ]
    
    if HYPEN_E_DOT in requirements:
        requirements.remove(HYPEN_E_DOT)
    return requirements

setup(
    name='Youtube Channel Analytics',
    version='0.1',
    author='Shruti kumari',
    author_email='shrutikumari0207@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt'),
)


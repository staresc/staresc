from setuptools import setup, find_packages

LONG_DESCRIPTION="""
Initially developed as an internal tool for [@5amu](https://github.com/5amu)'s
day job, thanks to [@cekout](https://github.com/cekout) it became clear that
the software could be generalized for a larger audience. So it became public.
The project is heavily inspired by [nuclei](https://github.com/projectdiscovery/nuclei),
but it targets another audience, such as professionals testing network
objects with SSH or Telnet credentials. 
"""

from staresc import VERSION

REQUIREMENTS = './requirements.txt'
try:
    with open(REQUIREMENTS, 'r') as req:
        requires = req.readlines()

except:
    requires = []
    print(f"[WARNING] could not find requirements file: {REQUIREMENTS}")


setup(
    name='staresc',
    version=f'{VERSION}',
    description='Staresc is a fast and reliable local vulnerability scanner',
    long_description=LONG_DESCRIPTION,
    author='Valerio Casalino, Davide Cecchini',
    author_email='casalinovalerio.cv@gmail.com, davidececchini97@gmail.com',
    url='https://github.com/staresc/staresc',
    license='GPLv3',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Security',
    ],
    keywords='staresc vulnerability scanner ssh telnet',
    packages=find_packages(),
    install_requires=requires,
    scripts=['scripts/staresc'],
)

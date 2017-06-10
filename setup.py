from setuptools import setup

setup(
    name='cliggle',
    version='0.2',
    author='Jay Karimi',
    author_email='jkarimi91@gmail.com',
    description='A CLI for Kaggle competitions.',
    license='MIT',
    url='https://github.com/jkarimi91/cliggle',
    keywords='kaggle cli',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Development Status :: 3 - Alpha'
    ],
    platforms=['Any'],

    packages=['cliggle'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        'click',
        'requests',
        'tqdm',
        'future'
    ],
    entry_points='''
        [console_scripts]
        cliggle=cliggle.cli:cliggle
    ''',
)

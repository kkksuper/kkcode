from setuptools import setup
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='kkcode',
    version='0.0.6',
    packages=['kkTools'],
    url='https://gitee.com/kksuperr/kkcode',
    license='MIT',
    author='Hanzhao Li',
    author_email='lihanzhao.mail@gmail.com',
    description='Some useful script for personal daily work.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['numpy'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
import setuptools

with open("Readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='kubeb',
    version='0.0.5',
    author="podder-ai",
    description=" Kubeb (Cubeba) provide CLI to build and deploy a application to Kubernetes environment",
    packages=setuptools.find_packages(),
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/podder-ai/kubeb",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'click',
        'jinja2',
        'pyyaml',
        'python-dotenv',
        'click-spinner',
    ],
    entry_points={
        'console_scripts': ['kubeb=kubeb.main:cli'],
    }
)
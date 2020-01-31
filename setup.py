import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tfex", # Replace with your own username
    version="0.0.1",
    author="Shawn Presser",
    author_email="shawnpresser@gmail.com",
    description="Sledgehammer for machine learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shawwn/tfex",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

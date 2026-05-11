from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="backdesk",
    version="0.0.1",
    description="Backdesk workspace customizations for ERPNext",
    author="Backdesk",
    author_email="hello@backdesk.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)

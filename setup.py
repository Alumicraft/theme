from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="monocore_theme",
    version="0.0.1",
    description="Monocore Theme - Custom UI customizations for ERPNext",
    author="Monocore",
    author_email="hello@monocore.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)

from setuptools import setup, find_packages

setup(
    name="ilastik-install",
    version="0.1.1dev0",
    author="Dominik Kutra",
    author_email="author email address",
    license="MIT",
    description="Make ilastik binary relocatable",
    # long_description=description,
    # url='https://...',
    package_dir={"": "src"},
    packages=find_packages("./src"),
    include_package_data=True,
    install_requires=[
        # 'dep1>=1.0,<2',
        # 'dep2>=2'
    ],
    entry_points={
        "console_scripts": ["ilastik-install = ilastik_install.__main__:main"]
    },
)

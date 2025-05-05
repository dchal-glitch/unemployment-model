from setuptools import setup, find_packages

setup(
    name="unemp_restructured",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "scikit-learn>=1.0.0",
        "cx_Oracle>=8.3.0",
        "sqlalchemy>=1.4.0",
        "matplotlib>=3.4.0",
        "flaml>=1.0.0",
        "darts>=0.20.0",
    ],
    author="SCAD Data Science Team",
    author_email="datascience@scad.ae",
    description="Unemployment Forecast Model",
    keywords="unemployment, forecast, model",
    python_requires=">=3.7",
)

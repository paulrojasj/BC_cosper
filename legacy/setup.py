from setuptools import setup, find_packages

setup(
    name="costo_personal",
    version="0.1.0",
    description="Sistema de reportería y métricas de costo de personal",
    author="Paul Rojas",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "python-dateutil>=2.8.2",
        "openpyxl>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
)

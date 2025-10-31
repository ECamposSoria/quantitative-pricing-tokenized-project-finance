from setuptools import setup, find_packages

setup(
    name="pftoken",
    version="0.1.0",
    description="Project Finance Tokenization Simulator (CFADS, waterfall, Monte Carlo, pricing, stress)",
    author="Christian Prete et al.",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "scipy",
        "matplotlib",
        "pytest",
        "jupyter",
        "numpy-financial",
        "eth-abi",
        "pydantic>=2.5",
    ],
    python_requires=">=3.10",
)

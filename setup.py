from setuptools import find_packages, setup

setup(
    name="elevenlabs-unleashed",
    packages=find_packages(exclude=[]),
    version="0.1.0",
    description="Unlimited access to Elevenlabs API",
    long_description_content_type="text/markdown",
    author="GaspardCulis",
    url="https://github.com/GaspardCulis/elevenlabs-unleashed",
    keywords=["artificial intelligence", "tts", "deep learning", "elevenlabs", "api", "unlimited"],
    install_requires=[
        "elevenlabs>=0.2.18",
        "selenium>=4.10.0",
        "names>=0.3.0",
        "requests>=2.31.0"
    ],
    classifiers=[
    ],
)
# setup.py
import codecs
with codecs.open('build.py', 'r') as build_file:
    build_source = build_file.read()
source = dict()
exec(build_source, source)
setup = source['setup']
def main() -> None:
    """Runs the function to distribute the package."""
    setup(
        package="socketos",
        exclude=[
            "__pycache__",
            "*.pyc"
        ],
        include=[],
        requirements="requirements.txt",
        dev_requirements="requirements-dev.txt",
        name='socket-os',
        version='0.0.0',
        description=(
            "A powerfull and flexible framework for designing async "
            "socket based data streaming and distribution systems, "
            "with automated parsing, dynamic data store and "
            "high-level control hooks."
        ),
        license='MIT',
        author="Shahaf Frank-Shapir",
        author_email='shahaffrs@gmail.com',
        url='https://github.com/Shahaf-F-S/socket-os',
        long_description_content_type="text/markdown",
        classifiers=[
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Operating System :: OS Independent"
        ]
    )
if __name__ == "__main__":
    main()

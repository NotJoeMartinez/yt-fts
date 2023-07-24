.PHONY: build install clean

# Build the package
build:
	python setup.py sdist bdist_wheel

# Install the package
install:
	pip install -e .

# Clean build artifacts
clean:
	rm -rf build dist *.egg-info
	pip uninstall yt-fts 
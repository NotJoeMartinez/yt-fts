.PHONY: build install clean test

build:
	python -m build

install:
	pip install .

clean:
	rm -rf build dist *.egg-info

test:
	pytest tests/
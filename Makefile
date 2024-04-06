.PHONY: build install clean test

build:
	python -m build

install:
	pip install -e .

clean:
	rm -rf build dist *.egg-info
	pip uninstall yt-fts

test:
	pytest tests/
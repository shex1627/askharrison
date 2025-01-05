.PHONY: build clean publish publish-test

# Clean previous builds
clean:
	rm -rf dist

# Build the package, make sure to have twine installed
build: clean
	python -m build

# Publish to PyPI
publish: build
	twine upload dist/*

# Publish to TestPyPI
publish-test: build
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*
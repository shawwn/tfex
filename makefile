.PHONY: all build clean test

MODS := tfex.x	\
	tfex/__init__.x

all: $(MODS:.x=.py)

clean:
	@rm -f dist/*

build: clean
	@python3 setup.py sdist bdist_wheel

test: all
	@echo tests:

testpypi: clean build
	@python3 -m twine upload --repository testpypi dist/*
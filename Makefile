.PHONY: all gerber clean
UNAME := $(shell uname)

all: gerber

gerber:
	@echo "Creating gerber files..."
ifeq ($(UNAME),Linux)
	python2 Tools/plot_gerber.py
endif
ifeq ($(UNAME),Darwin)
	/Applications/Kicad/kicad.app/Contents/Frameworks/Python.framework/Versions/2.7/bin/python2.7 Tools/plot_gerber.py
endif

clean:
	@echo "Cleaning up..."
	rm -rf gerber

# Copyright (c) 2026 Taras Bulubas. All rights reserved.
# Use requires prior written permission; see LICENSE.

# Development tasks for the tennis line sweeping project (GNU make).
#
# Works on Windows (recipes run in cmd.exe, also when make is started from
# PowerShell or Git Bash) and on Linux/macOS.
#
#   make venv      create .venv and install the project with all extras
#   make test      run the tests
#   make run       solve an example instance (override with ARGS="...")
#   make image     render images/line-sweeping-linkedin.png
#   make notebook  open notebooks/line_sweeping.ipynb in JupyterLab
#
# The project uses Python 3.12 (PYTHON_VERSION). The base interpreter is found
# with the py launcher on Windows and as python3.12 elsewhere, independently of
# which python comes first on the PATH.

PYTHON_VERSION := 3.12

ifeq ($(OS),Windows_NT)
    SHELL := cmd.exe
    .SHELLFLAGS := /c
    PYTHON := py -$(PYTHON_VERSION)
    VENV_PY := .venv\Scripts\python.exe
else
    PYTHON := python$(PYTHON_VERSION)
    VENV_PY := .venv/bin/python
endif

VENV_CFG := .venv/pyvenv.cfg
STAMP := .venv/.installed
ARGS ?= -x 5.485 -y -6.4

.DEFAULT_GOAL := help
.PHONY: help venv test run image notebook notebook-check clean distclean recreate

help:
	@echo Targets:
	@echo   make venv       create .venv and install the project with all extras
	@echo   make test       run the tests with pytest
	@echo   make run        solve an example; override the broom place with ARGS="-x ... -y ..."
	@echo   make image      render images/line-sweeping-linkedin.png
	@echo   make notebook   open notebooks/line_sweeping.ipynb in JupyterLab
	@echo   make notebook-check  run all notebook cells headless and store the outputs
	@echo   make clean      remove caches and build metadata
	@echo   make distclean  clean and remove .venv
	@echo   make recreate   distclean, then venv
	@echo Python $(PYTHON_VERSION), base interpreter: $(PYTHON)

# .venv is created only once. Re-creating an existing one would overwrite its
# python.exe, which fails while an IDE or a Jupyter kernel is using it.
$(VENV_CFG):
	$(PYTHON) scripts/check_venv.py $(PYTHON_VERSION)
	$(PYTHON) -m venv .venv

# The stamp file is rewritten after every install, so the packages are
# refreshed whenever pyproject.toml or this Makefile changes. An existing
# .venv of another Python version is never upgraded in place: check_venv.py
# stops with a hint to run make recreate.
$(STAMP): pyproject.toml Makefile $(VENV_CFG)
	$(PYTHON) scripts/check_venv.py $(PYTHON_VERSION)
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -e ".[dev,plot,notebook]"
	$(VENV_PY) -c "open('$(STAMP)', 'w').close()"

venv: $(STAMP)

test: $(STAMP)
	$(VENV_PY) -m pytest

run: $(STAMP)
	$(VENV_PY) -m line_sweeping $(ARGS)

image: $(STAMP)
	$(VENV_PY) scripts/linkedin_image.py

notebook: $(STAMP)
	$(VENV_PY) -m jupyter lab notebooks/line_sweeping.ipynb

notebook-check: $(STAMP)
	$(VENV_PY) -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.record_timing=False notebooks/line_sweeping.ipynb

clean:
	$(PYTHON) -c "import glob, shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', 'build', *glob.glob('src/*.egg-info'), *glob.glob('*/**/__pycache__', recursive=True)]]"

distclean: clean
	$(PYTHON) -c "import shutil; shutil.rmtree('.venv', ignore_errors=True)"

recreate: distclean
	$(MAKE) venv

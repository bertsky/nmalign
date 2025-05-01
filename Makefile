PYTHON = python3
PIP = pip3
PYTHONIOENCODING=utf8
GIT_SUBMODULE = git submodule

DOCKER_BASE_IMAGE ?= docker.io/ocrd/core:latest
DOCKER_TAG ?= ocrd/nmalign
DOCKER ?= docker
PYTEST_ARGS ?= -vv

help:
	@echo
	@echo "  Targets"
	@echo
	@echo "    deps        (install required Python packages via pip)"
	@echo "    install     (install this Python package via pip)"
	@echo "    install-dev (install in editable mode)"
	@echo "    build       (build Python source and binary dist)"
	@echo "    docker      (build Docker image $(DOCKER_TAG) from $(DOCKER_BASE_IMAGE))"
	@echo "    test        (run tests via Pytest)"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    PYTHON        [$(PYTHON)]"
	@echo "    PIP           [$(PIP)]"
	@echo "    PYTEST_ARGS   (additional arguments for Pytest [$(PYTEST_ARGS)]"
	@echo "    DOCKER_TAG    (tag of Docker image to build [$(DOCKER_TAG)])"

# Install Python deps via pip
deps:
	$(PIP) install -r requirements.txt

# Install Python package via pip
install:
	$(PIP) install .

install-dev:
	$(PIP) install -e .

build:
	$(PIP) install build wheel
	$(PYTHON) -m build .

deps-test:
	$(PIP) install -r requirements-test.txt

test: tests/assets
	$(PYTHON) -m pytest  tests --durations=0 $(PYTEST_ARGS)

coverage:
	coverage erase
	$(MAKE) test PYTHON="coverage run"
	coverage report -m

# Update OCR-D/assets submodule
.PHONY: always-update tests/assets
testdata: always-update
	$(GIT_SUBMODULE) sync --recursive $@
	if $(GIT_SUBMODULE) status --recursive $@ | grep -qv '^ '; then \
		$(GIT_SUBMODULE) update --init --recursive $@ && \
		touch $@; \
	fi

# Setup test assets
tests/assets: testdata
	mkdir -p $@
	cp -a $</data/* $@

docker:
	$(DOCKER) build \
	--build-arg DOCKER_BASE_IMAGE=$(DOCKER_BASE_IMAGE) \
	--build-arg VCS_REF=$$(git rev-parse --short HEAD) \
	--build-arg BUILD_DATE=$$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
	-t $(DOCKER_TAG) .

.PHONY: help coverage deps deps-test install install-dev build docker

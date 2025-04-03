PYTHON = python3
PIP = pip3
PYTHONIOENCODING=utf8

DOCKER_BASE_IMAGE = docker.io/ocrd/core:v3.3.0
DOCKER_TAG = ocrd/nmalign

help:
	@echo
	@echo "  Targets"
	@echo
	@echo "    deps        (install required Python packages via pip)"
	@echo "    install     (install this Python package via pip)"
	@echo "    install-dev (install in editable mode)"
	@echo "    build       (build Python source and binary dist)"
	@echo "    docker      (build Docker image $(DOCKER_TAG) from $(DOCKER_BASE_IMAGE))"

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

docker:
	docker build \
	--build-arg DOCKER_BASE_IMAGE=$(DOCKER_BASE_IMAGE) \
	--build-arg VCS_REF=$$(git rev-parse --short HEAD) \
	--build-arg BUILD_DATE=$$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
	-t $(DOCKER_TAG) .

.PHONY: help deps install install-dev build docker

ARG DOCKER_BASE_IMAGE
FROM $DOCKER_BASE_IMAGE
ARG VCS_REF
ARG BUILD_DATE
LABEL \
    maintainer="https://ocr-d.de/kontakt" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/bertsky/nmalign" \
    org.label-schema.build-date=$BUILD_DATE

WORKDIR /build/nmalign
COPY setup.py .
COPY nmalign/ocrd-tool.json .
COPY nmalign ./nmalign
COPY requirements.txt .
COPY README.md .
COPY Makefile .
RUN make install
RUN rm -rf /build/nmalign

WORKDIR /data
VOLUME ["/data"]

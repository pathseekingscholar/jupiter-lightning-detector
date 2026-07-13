FROM condaforge/miniforge3:latest

ARG ISIS_VERSION=10.0.0

RUN mamba create --yes --prefix /opt/isis \
      --channel usgs-astrogeology \
      --channel conda-forge \
      "isis=${ISIS_VERSION}" \
    && mamba clean --all --yes

RUN ln --symbolic /opt/isis/lib/libcsmapi.so.3.0.3 /opt/isis/lib/libcsmapi.so.3

ENV ISISROOT=/opt/isis
ENV ISISDATA=/isisdata
ENV PATH=/opt/isis/bin:${PATH}
ENV LD_LIBRARY_PATH=/opt/isis/lib

WORKDIR /workspace

LABEL org.opencontainers.image.title="Jupiter Lightning Detector ISIS runtime"
LABEL org.opencontainers.image.source="https://github.com/pathseekingscholar/jupiter-lightning-detector"

ARG ubuntu_version
FROM ubuntu:${ubuntu_version} as builder

# docker build --build-arg ubuntu_version 22.04 -t ghcr.io/buildsi/splice-experiment-runs .

ENV DEBIAN_FRONTEND=noninteractive
ENV org.opencontainers.image.source="https://github.com/buildsi/splice-experiment-runs"
ARG LIBRARY_VERSION=2.0
RUN apt-get update && apt-get install -y build-essential \
    curl \
    libelf-dev \
    libzip-dev \
    autoconf \
    libtool \
    pkg-config \
    libxml2 \
    libxml2-dev \
    elfutils \
    doxygen \
    wget \
    git \
    libdw-dev \
    elfutils \
    python3-lxml \
    python3 \
    python3-dev \
    python3-sphinx \
    python3-pip \
    g++

RUN ldconfig && \ 
    wget http://mirrors.kernel.org/sourceware/libabigail/libabigail-${LIBRARY_VERSION}.tar.gz && \
    tar -xvf libabigail-${LIBRARY_VERSION}.tar.gz && \
    cd libabigail-${LIBRARY_VERSION} && \
    autoreconf -fi && \
    mkdir build && \
    cd build && \
    ../configure --prefix=/usr/local && \
    make all install && \
    ldconfig    

COPY ./install_ubuntu_deps.sh /install-ubuntu-deps.sh
RUN /bin/bash /install-ubuntu-deps.sh

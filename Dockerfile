FROM ubuntu:focal

ARG UNAME=buildroot
ARG BUILDROOT_VER=2021.02
ARG UID=1000
ARG GID=1000

# install applications
RUN apt-get update
RUN apt-get install -y \
    sudo build-essential file wget cpio unzip rsync bc locales libncurses-dev vim python3 git

# set the locale
RUN locale-gen en_US.UTF-8
RUN update-locale

# Download BuildRoot
WORKDIR /usr/src
RUN git clone --depth 1 --branch $BUILDROOT_VER https://github.com/buildroot/buildroot buildroot && \
    cd buildroot

# create new user
RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash -G sudo $UNAME
# set root password
RUN echo "$UNAME:root" | chpasswd

USER $UNAME
WORKDIR /home/$UNAME/src

FROM ubuntu:18.04


# Install singularity

ENV SINGULARITY_VERSION "2.5.0"
ENV NUM_CPU 16
ENV CI_PROJECT_DIR /tmp
ENV LANG en_US.utf8

# Enable universe repos and update the repos to point to RIT https mirrors
RUN sed -i "/^# deb.*universe/ s/^# //" /etc/apt/sources.list
RUN sed -r -i "s/https?:\/\/archive.ubuntu.com/http:\/\/mirrors.rit.edu/g" /etc/apt/sources.list
RUN sed -r -i "s/https?:\/\/security.ubuntu.com/http:\/\/mirrors.rit.edu/g" /etc/apt/sources.list

# Install everything nessesary to build singularity
RUN apt-get update && apt-get install -y \
    # From singularity
    python \
    dh-autoreconf \
    build-essential \
    squashfs-tools \
    uuid-dev \
    libssl-dev \
    libarchive-dev \
    make \
    wget \
    tar \
    git \
    # From build_template
    python3 \
    openssh-client \
    rsync \
    sudo \
    language-pack-en \
    make

RUN wget --no-check-certificate https://github.com/singularityware/singularity/releases/download/$SINGULARITY_VERSION/singularity-$SINGULARITY_VERSION.tar.gz
RUN tar xvf singularity-$SINGULARITY_VERSION.tar.gz

RUN cd singularity-$SINGULARITY_VERSION && \
    ./configure && \
    make -j$NUM_CPU && \
    make install

# Install the project and its dependencies

RUN apt-get install -y \
    python3 \
    python3-pip

RUN mkdir -p /data
RUN pip3 install pipenv gunicorn

ADD . /data

CMD cd /data/web && pipenv install && pipenv run python app.py

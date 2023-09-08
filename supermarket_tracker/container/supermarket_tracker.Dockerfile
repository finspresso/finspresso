FROM ubuntu:22.04
LABEL maintainer "Jon Lemonade <jon.lemonade@finspresso.com>"

WORKDIR /

RUN apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y \
        make \
        build-essential \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        wget \
        curl \
        llvm \
        libncurses5-dev \
        libncursesw5-dev \
        xz-utils \
        tk-dev \
        libffi-dev \
        liblzma-dev \
        git

RUN git clone https://github.com/pyenv/pyenv.git /pyenv
ENV PYENV_ROOT /pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN pyenv install 3.8.5

RUN echo 'eval "$(pyenv init -)"' >> /root/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> /root/.profile

RUN pyenv global 3.8.5

RUN mkdir /var/supermarket_tracker
COPY supermarket_tracker.py /var/supermarket_tracker/
COPY requirements.txt /var/supermarket_tracker/

RUN pip install --upgrade pip
RUN pip install -r /var/supermarket_tracker/requirements.txt





#ENTRYPOINT ["pyenv", "init", "-"]
# ENTRYPOINT ["ls", "-la" ]
# ENTRYPOINT ["pyenv init"]

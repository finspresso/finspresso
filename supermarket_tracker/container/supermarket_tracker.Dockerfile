FROM ubuntu:22.04
LABEL maintainer "Jon Lemonade <jon.lemonade@finspresso.com>"

WORKDIR /
ARG GH_TOKEN_ARG
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

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y vim

RUN git clone https://github.com/pyenv/pyenv.git /pyenv
ENV PYENV_ROOT /pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN pyenv install 3.8.5

RUN echo 'eval "$(pyenv init -)"' >> /root/.bashrc
RUN echo 'eval "$(pyenv init -)"' >> /root/.profile

RUN pyenv global 3.8.5

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /google-chrome.deb

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y /google-chrome.deb --fix-missing

RUN mkdir /var/supermarket_tracker
COPY requirements.txt /var/supermarket_tracker/
RUN pip install --upgrade pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y default-libmysqlclient-dev
RUN pip install -r /var/supermarket_tracker/requirements.txt
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y git

RUN wget https://github.com/cli/cli/releases/download/v2.34.0/gh_2.34.0_linux_amd64.deb -O gh_amd64.deb
RUN apt install ./gh_amd64.deb && rm ./gh_amd64.deb


ENV GH_TOKEN=$GH_TOKEN_ARG
ENV BASE_BRANCH="feature/docker_compose"
RUN git clone --branch ${BASE_BRANCH} --recursive https://github.com/finspresso/finspresso.git /var/finspresso

ENV FINSPRESSO_ROOT="/var/finspresso"
RUN pip install $FINSPRESSO_ROOT/db_interface_package

RUN mkdir -p $FINSPRESSO_ROOT/supermarket_tracker/
RUN mkdir -p $FINSPRESSO_ROOT/supermarket_tracker/configs
RUN mkdir -p $FINSPRESSO_ROOT/references/mbudget/
COPY configs/mbudget.json $FINSPRESSO_ROOT/supermarket_tracker/configs/
COPY references/mbudget/product_reference.json $FINSPRESSO_ROOT/supermarket_tracker/references/mbudget/

COPY credentials/sql_credentials_docker.json $FINSPRESSO_ROOT/supermarket_tracker/credentials/sql_credentials.json
COPY container/entrypoint_supermarket.sh /
ARG USER_EMAIL
ARG USER_NAME
RUN git config --global user.email $USER_EMAIL
RUN git config --global user.name $USER_NAME
RUN cd $FINSPRESSO_ROOT && git remote set-url origin https://finspresso:$GH_TOKEN@github.com/finspresso/finspresso.git
RUN cd $FINSPRESSO_ROOT && pre-commit install
ENTRYPOINT ["sh", "-c", "$FINSPRESSO_ROOT/supermarket_tracker/container/entrypoint_supermarket.sh"]

#Next: Run update_all.sh in docker container: 1) Enable commit and push or auto-creation of PR with new product_reference.json via github cli (only create PR if there was a change) 2) Upload to MySQL docker db 3) Upload to MySQL finpresso db
# 4) Add volume to store screenshots for later storing them

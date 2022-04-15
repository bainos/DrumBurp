FROM ubuntu:18.04

USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y openssh-server
RUN apt-get install -y git vim python2.7 python-qt4
RUN apt-get install -y build-essential python-dev
RUN apt-get install -y liblzma-dev patchelf
RUN wget https://bootstrap.pypa.io/pip/2.7/get-pip.py
RUN python get-pip.py

RUN mkdir /var/run/sshd
RUN mkdir /root/.ssh
COPY conf.d/sshd_config /etc/ssh/sshd_config

RUN mkdir /root/DrumBurp
COPY . /root/DrumBurp/
RUN pip install -r /root/DrumBurp/requirements-dev.txt

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/*

EXPOSE 22
COPY conf.d/entrypoint.sh /
ENTRYPOINT []
CMD ["/bin/bash","/entrypoint.sh"]

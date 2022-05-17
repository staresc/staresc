# Run with docker run -it -d --rm -p 22:10024 -p 23:10025 <name> 
FROM ubuntu:20.04
MAINTAINER 5amu

ENV LC_CTYPE C.UTF-8
ARG DEBIAN_FRONTEND=noninteractive

# Install vulnerable sudo version
# https://github.com/LiveOverflow/pwnedit/blob/main/episode01/Dockerfile
RUN apt-get -yq update && apt-get install -yq gcc make wget curl git vim gdb clang llvm python3 python3-pip bsdmainutils
RUN cd /root/ && wget https://www.sudo.ws/dist/sudo-1.8.31p2.tar.gz && tar -xvf sudo-1.8.31p2.tar.gz && cd sudo-1.8.31p2 && ./configure && make && make install

# Install other packages to be reviewed by staresc
RUN apt-get -yq install ssh telnetd xinetd lxc python2
RUN echo "service telnet\n{\ndisable = no\nflags = REUSE\nsocket_type = stream\nwait = no\nuser = root\nserver = /usr/sbin/in.telnetd\nlog_on_failure += USERID\n}" > /etc/xinetd.d/telnet

# Add user to the container with password "pass"
RUN useradd -p '$1$MNXuasE0$Sx3ONMuFhF9iV11IUwzNz1' -ms /bin/bash user
RUN echo 'export PS1="\[\e]0;\u@\h: \w\a\]\[\033[01;31m\]\u\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]# "' >> /root/.bashrc
RUN echo 'export PS1="\[\e]0;\u@\h: \w\a\]\[\033[01;32m\]\u\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]$ "' >> /home/user/.bashrc

# Create private key for staresc to find
USER user
RUN ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519

# Entrypoint to sshd and telnet
USER root
EXPOSE 22
EXPOSE 23

# Set root password to "toor"
RUN sed -i "s/root:\*/root:\$6\$msg7fWs4mQJehet\/\$cbm2Yf1BYzPeFkYENkKFmXUNw5SyKqiovjvYAF1KMlbEojplbYaGZ9GSDvyw8b9ej8nwfbr4W5t4aokk6uvJR./g" /etc/shadow

ENTRYPOINT service ssh restart && /etc/init.d/xinetd restart && tail -f /dev/null

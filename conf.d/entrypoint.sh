#!/bin/sh
/usr/sbin/sshd -D -f /etc/ssh/sshd_config \
  -E /var/log/sshd.log

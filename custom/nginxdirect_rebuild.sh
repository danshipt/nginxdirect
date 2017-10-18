#!/bin/bash

if [ -z $1 ]; then
    echo "User name?"
    exit 1
fi

python2.7 /usr/local/nginxdirect/nginxvhostctl.py -o /etc/nginx/hosting --rebuild $1 >>/var/log/nginxdirect.log 2>&1
if [ $? -gt 0 ]; then
    exit 1
fi

/etc/init.d/httpd configtest >/dev/null 2>&1
if [ $? -gt 0 ]; then
    exit 1;
else
    /etc/init.d/httpd reload >/dev/null 2>&1
fi

/etc/init.d/nginx configtest >/dev/null 2>&1
if [ $? -gt 0 ]; then
    exit 1;
else
    /etc/init.d/nginx reload >/dev/null 2>&1
fi

exit 0

#!/bin/sh
PATH=$PATH:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin
LANG=C
export LANG
export PATH

#/usr/local/directadmin/scripts/custom/generate_map.pl -as $username $domain $subdomain
#if [ $? -gt 0 ]; then
#    exit 1;
#fi
#/etc/init.d/nginx  configtest > /dev/null
#if [ $? -gt 0 ]; then
#    exit 1;
#else
#    /etc/init.d/nginx reload
#fi

/usr/local/directadmin/scripts/custom/nginxdirect_rebuild.sh $username
if [ $? -gt 0 ]; then
    exit 1;
fi

exit 0;


#!/bin/sh
PATH=$PATH:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin
LANG=C
export LANG
export PATH

/usr/local/directadmin/scripts/custom/nginxdirect_rebuild.sh ${username}
if [ $? -gt 0 ]; then
    exit 1;
fi

exit 0;


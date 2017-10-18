DirectAdmin, Apache and Nginx integration. It generates map files
for Nginx to parametrize virtual hosts. SSL supported.

Requirements:
* Python 2.7+

Usage: nginxvhostctl.py [-h] -o OUT_CONFIG_DIR [-s DA_USERS_CONFIG_DIR]
[--rebuild-all | -r REBUILD_USER | -d DELETE_USER]

Arguments:

  -h, --help            show this help message and exit
  
  -o OUT_CONFIG_DIR, --out-dir OUT_CONFIG_DIR
                        Directory with generated Nginx config files (default:
                        None)
                        
  -s DA_USERS_CONFIG_DIR, --da-users-config DA_USERS_CONFIG_DIR
                        DirectAdmin users config root (default:
                        /usr/local/directadmin/data/users)
                        
  --rebuild-all         Rebuild vhosts using DirectAdmin user configs for all
                        users (default: False)
                        
  -r REBUILD_USER, --rebuild REBUILD_USER
                        Rebuild vhosts using DirectAdmin user configs for the
                        specific user (default: None)
                        
  -d DELETE_USER, --delete DELETE_USER
                        Rebuild vhosts using DirectAdmin user configs for the
                        specific user (default: None)


## Install

1. mkdir -p /etc/nginx/hosting/https
2. cp ./conf.sample/vhost_*.conf /etc/nginx/
3. Check ./conf.sample/nginx.conf and update your nginx.conf.
Test config after changes:
```bash
nginx -t
```

4. Put code into /usr/local/nginxdirect/
5. Put /custom/ contents to /usr/local/directadmin/scripts/custom/ 
6. Generate initial maps and configs:

```bash
python2.7 /usr/local/nginxdirect/nginxvhostctl.py -o /etc/nginx/hosting --rebuild-all
```

7. Change SSL config of the Apache: set port to 8443
8. Update virtual DirectAdmin host templates here 
/usr/local/directadmin/data/templates/custom. Change IP address to APACHE_IP:8443.
Run:
```bash
echo "action=rewrite&value=httpd" >> /usr/local/directadmin/data/task.queue
```
9. Restart nginx and Apache.

### Sample usage: rebuild config for user

```bash
#!/bin/bash

if [ -z $1 ]; then
    echo "User name?"
    exit 1
fi

python2.7 /usr/local/nginxdirect/nginxvhostctl.py -o /etc/nginx/hosting --rebuild $1 >>/var/log/nginxdirect.log 2>&1
if [ $? -gt 0 ]; then
    exit 1
fi

exit 0
```

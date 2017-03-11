Script is used for DirectAdmin and Nginx integration. It generates map files
for Nginx to parametrize virtual hosts. It supports SSL.

usage: nginxvhostctl.py [-h] -o OUT_CONFIG_DIR [-s DA_USERS_CONFIG_DIR]
[--rebuild-all | -r REBUILD_USER | -d DELETE_USER]

Nginx virtualhosts updater

optional arguments:
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

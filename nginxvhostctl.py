# Copyright (C) 2015 JustHost.ru, Dmitry Shilyaev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Script is used for DirectAdmin and Nginx integration. It generates map files
# for Nginx to parametrize virtual hosts. It supports SSL.
#
# usage: nginxvhostctl.py [-h] -o OUT_CONFIG_DIR [-s DA_USERS_CONFIG_DIR]
# [--rebuild-all | -r REBUILD_USER | -d DELETE_USER]
#
# Nginx virtualhosts updater
#
# optional arguments:
#   -h, --help            show this help message and exit
#   -o OUT_CONFIG_DIR, --out-dir OUT_CONFIG_DIR
#                         Directory with generated Nginx config files (default:
#                         None)
#   -s DA_USERS_CONFIG_DIR, --da-users-config DA_USERS_CONFIG_DIR
#                         DirectAdmin users config root (default:
#                         /usr/local/directadmin/data/users)
#   --rebuild-all         Rebuild vhosts using DirectAdmin user configs for all
#                         users (default: False)
#   -r REBUILD_USER, --rebuild REBUILD_USER
#                         Rebuild vhosts using DirectAdmin user configs for the
#                         specific user (default: None)
#   -d DELETE_USER, --delete DELETE_USER
#                         Rebuild vhosts using DirectAdmin user configs for the
#                         specific user (default: None)
#
import argparse
import exceptions
import errno
import os
import sys
import traceback
import fcntl

from nginxlib import NginxMap
from diradminlib import DirectAdminUserConfig


def safe_create_path(path, mode=0o711):
    if not path:
        raise exceptions.ValueError("path")

    if os.path.exists(path):
        return True

    try:
        os.makedirs(path, mode)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

    return True


class NginxVhostsConfigManager:
    MAP_USERS_NAME = 'map_users.conf'
    MAP_DOMAINS_NAME = 'map_domains.conf'
    MAP_SUBDOMAINS_NAME = 'map_subdomains.conf'

    def __init__(self, working_dir, source_da_dir):
        if not os.path.exists(working_dir):
            raise Exception("Map files dir must exist: %s" % working_dir)

        if not os.path.exists(source_da_dir):
            raise Exception("DirectAdmin user config dir must exist: %s" % source_da_dir)

        self.working_dir = working_dir
        self.tpl_ssl_vhost_file_name = os.path.join(os.path.dirname(__file__), 'vhost_ssl.conf.tpl')
        if not os.path.exists(self.tpl_ssl_vhost_file_name):
            raise Exception("Place Nginx vhost template in the correct location: %s" % self.tpl_ssl_vhost_file_name)

        self.source_da_dir = source_da_dir
        self.map_users = NginxMap('http_host', 'user')
        self.map_domains = NginxMap('http_host', 'domain')
        self.map_subdomains = NginxMap('http_host', 'subdomain')

        self._load()

    def _load(self):
        if os.path.exists(os.path.join(self.working_dir, self.MAP_USERS_NAME)):
            self.map_users.load(os.path.join(self.working_dir, self.MAP_USERS_NAME))

        if os.path.exists(os.path.join(self.working_dir, self.MAP_DOMAINS_NAME)):
            self.map_domains.load(os.path.join(self.working_dir, self.MAP_DOMAINS_NAME))

        if os.path.exists(os.path.join(self.working_dir, self.MAP_SUBDOMAINS_NAME)):
            self.map_subdomains.load(os.path.join(self.working_dir, self.MAP_SUBDOMAINS_NAME))

    def _save(self):
        # save all maps
        self.map_users.save(os.path.join(self.working_dir, self.MAP_USERS_NAME))
        self.map_domains.save(os.path.join(self.working_dir, self.MAP_DOMAINS_NAME))
        self.map_subdomains.save(os.path.join(self.working_dir, self.MAP_SUBDOMAINS_NAME))

    def _add_domain(self, domain_name, user_name):
        assert domain_name, "Domain name must be specified"
        assert user_name, "User name must be specified"

        domain_key = ".%s" % domain_name
        self.map_users.add_item(domain_key, '"%s"' % user_name)
        self.map_domains.add_item(domain_key, '"%s"' % domain_name)

    def _add_domain_alias(self, domain_name, domain_alias, user_name):
        assert domain_name, "Domain name must be specified"
        assert domain_alias, "Domain alias must be specified"
        assert user_name, "User name must be specified"

        self.map_users.add_item(".%s" % domain_alias, '"%s"' % user_name)
        self.map_domains.add_item(".%s" % domain_alias, '"%s"' % domain_name)

    def _add_subdomain(self, domain_name, subdomain):
        assert domain_name, "Domain name must be specified"
        assert subdomain, "Subdomain must be specified"

        self.map_subdomains.add_item(".%s.%s" % (subdomain, domain_name), '"%s"' % subdomain)

    def _get_https_vhost_config(self, domain_name):
        """
        Returns path to https vhost config file
        :param domain_name: Domain name of the https vhost
        :return: path to https vhost config file
        """
        assert domain_name, "Domain name must be specified"

        ssl_vhosts_drop_dir = os.path.join(self.working_dir, 'https')

        safe_create_path(ssl_vhosts_drop_dir)

        return os.path.join(ssl_vhosts_drop_dir, "%s.conf" % domain_name)

    def clean_unresolved_domains(self):
        """
        Remove domains that is don't appears in map_users
        :return:
        """
        for domain_name in list(self.map_domains.items):
            if domain_name not in self.map_users.items:
                self.map_domains.del_item(domain_name)

                for subdomain_domain_name in list(self.map_subdomains.items):
                    if subdomain_domain_name.endswith(domain_name):
                        self.map_subdomains.del_item(subdomain_domain_name)

                # remove https configs for all domains
                https_vhost_file = self._get_https_vhost_config(domain_name[1:])
                if os.path.exists(https_vhost_file):
                    os.remove(https_vhost_file)

        self._save()

    def delete_user(self, user_name):
        """
        Delete user configs from maps and https vhosts
        :param user_name:
        :return:
        """
        assert user_name, "User name must be specified"

        print "Deleting user: %s" % user_name

        # remove from maps
        for domain_name in self.map_users.find_keys_by_value('"%s"' % user_name):
            # remove domains and aliases
            for domain_domain_name in self.map_domains.find_keys_by_value('"%s"' % domain_name[1:]):
                self.map_domains.del_item(domain_domain_name)

            # remove subdomains
            for subdomain_domain_name in list(self.map_subdomains.items):
                if subdomain_domain_name.endswith(domain_name):
                    self.map_subdomains.del_item(subdomain_domain_name)

            # remove user domain
            self.map_users.del_item(domain_name)

            # remove https configs for all domains
            https_vhost_file = self._get_https_vhost_config(domain_name[1:])
            if os.path.exists(https_vhost_file):
                os.remove(https_vhost_file)

        self._save()

    def rebuild_user(self, user_name):
        """
        Rebuild Nginx vhost configs for the specific user from DirectAdmin
        user_name: name of DirectAdmin user to update
        """
        assert user_name, "User name must be specified"

        print "Rebuilding user: %s" % user_name
        user_dir = os.path.join(self.source_da_dir, user_name)
        if not os.path.exists(user_dir):
            raise Exception("Missing DirectAdmin user dir: %s" % user_dir)

        if os.path.isdir(user_dir):
            da_user_config = DirectAdminUserConfig(user_dir)

            for domain in da_user_config.get_domains():
                self._add_domain(domain.domain_name, da_user_config.user_name)

                current_pointers = []
                for domain_pointer in domain.get_pointers():
                    self._add_domain_alias(domain.domain_name, domain_pointer, da_user_config.user_name)
                    current_pointers.append(domain_pointer)

                for subdomain in domain.get_subdomains():
                    self._add_subdomain(domain.domain_name, subdomain)

                config = domain.get_config()
                if config.has_key('SSLCertificateFile') and config.has_key('SSLCertificateKeyFile'):
                    cert_file = config['SSLCertificateFile']
                    key_file = config['SSLCertificateKeyFile']

                    with open(self._get_https_vhost_config(domain.domain_name), 'w') as vhost_file:
                        fcntl.flock(vhost_file, fcntl.LOCK_EX)
                        for tpl_line in file(self.tpl_ssl_vhost_file_name):
                            tpl_line = tpl_line.replace('{sslkey}', key_file)
                            tpl_line = tpl_line.replace('{sslcrt}', cert_file)
                            tpl_line = tpl_line.replace('{user}', user_name)
                            tpl_line = tpl_line.replace('{domain}', domain.domain_name)
                            vhost_file.write(tpl_line)

            self._save()

    def rebuild_all(self):
        """
        Rebuild Nginx vhost configs for all users from DirectAdmin
        """
        if not os.path.exists(self.source_da_dir):
            raise Exception("DirectAdmin users config dir must exist: %s" % self.source_da_dir)

        for user_name in os.listdir(self.source_da_dir):
            self.delete_user(user_name)
            self.rebuild_user(user_name)

        self._save()


def main():
    parser = argparse.ArgumentParser(description='Nginx virtualhosts updater',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-o", "--out-dir", dest="out_config_dir", required=True,
                        help="Directory with generated Nginx config files")
    parser.add_argument("-s", "--da-users-config", dest="da_users_config_dir",
                        default='/usr/local/directadmin/data/users',
                        help="DirectAdmin users config root")

    mutual_group = parser.add_mutually_exclusive_group()
    mutual_group.add_argument('--rebuild-all', action='store_true',
                              help='Rebuild vhosts using DirectAdmin user configs for all users')
    mutual_group.add_argument('-r', '--rebuild', dest="rebuild_user",
                              help='Rebuild vhosts using DirectAdmin user configs for the specific user')
    mutual_group.add_argument('-d', '--delete', dest="delete_user",
                              help='Rebuild vhosts using DirectAdmin user configs for the specific user')

    args = parser.parse_args()

    # validate global args
    if not os.path.exists(args.out_config_dir):
        raise Exception("Directory must exist: %s" % args.out_config_dir)

    if not os.path.exists(args.da_users_config_dir):
        raise Exception("Directory must exist: %s" % args.da_users_config_dir)

    # dispatch
    conf_manager = NginxVhostsConfigManager(args.out_config_dir, args.da_users_config_dir)

    print "Updating Nginx vhosts config:"
    print "    Nginx config dir: %s" % args.out_config_dir
    print "    DirectAdmin users config dir: %s" % args.da_users_config_dir

    conf_manager.clean_unresolved_domains()

    if args.rebuild_all:
        conf_manager.rebuild_all()
    else:
        if args.delete_user:
            conf_manager.delete_user(args.delete_user)
        else:
            conf_manager.delete_user(args.rebuild_user)
            conf_manager.rebuild_user(args.rebuild_user)


if __name__ == "__main__":
    try:
        main()
    except Exception, ex:
        traceback.print_exc(file=sys.stdout)
        exit(1)

    exit(0)
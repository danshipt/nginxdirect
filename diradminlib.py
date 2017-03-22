import os
import fcntl


def uniq_list(list_obj):
    ptr_map = {}
    for elem in list_obj:
        ptr_map[elem] = elem

    return sorted(ptr_map.keys())


class DirectAdminUserDomain(object):
    """
    Configuration of DirectAdmin domain
    """

    def __init__(self, user_config, domain_name):
        assert user_config, "DirectAdmin directory object must be specified"
        assert domain_name, "Domain name must be specified"

        self.user_config = user_config
        self.domain_name = domain_name
        self.config = {}
        self.pointers = []
        self.subdomains = []
        self.ips = []

        self._load_subdomains()
        self._load_pointers()
        self._load_ips()
        self._load_config()

    def _load_config(self):
        domain_config_file = os.path.join(self.user_config.user_dir, 'domains', "%s.conf" % self.domain_name)
        if os.path.exists(domain_config_file):
            with open(domain_config_file, 'r') as fd_domain_config_file:
                fcntl.flock(fd_domain_config_file, fcntl.LOCK_EX)

                for domain_config in fd_domain_config_file:
                    domain_config = domain_config.strip()
                    conf_key, conf_value = domain_config.split('=')

                    self.config[conf_key] = conf_value

    def _load_pointers(self):
        pointers_file = os.path.join(self.user_config.user_dir, 'domains', "%s.pointers" % self.domain_name)
        if os.path.exists(pointers_file):
            new_pointers = []

            with open(pointers_file, 'r') as fd_pointers_file:
                fcntl.flock(fd_pointers_file, fcntl.LOCK_EX)

                for domain_pointer_info in fd_pointers_file:
                    domain_pointer_info = domain_pointer_info.strip()
                    domain_pointer, point_type = domain_pointer_info.split('=')
                    new_pointers.append(domain_pointer)

            self.pointers = uniq_list(self.pointers + new_pointers)

    def _load_subdomains(self):
        subdomains_file = os.path.join(self.user_config.user_dir, 'domains', "%s.subdomains" % self.domain_name)
        if os.path.exists(subdomains_file):
            new_subdomains = []

            with open(subdomains_file, 'r') as fd_subdomains_file:
                fcntl.flock(fd_subdomains_file, fcntl.LOCK_EX)

                for subdomain in fd_subdomains_file:
                    subdomain = subdomain.strip()
                    new_subdomains.append(subdomain)

            self.subdomains = uniq_list(self.subdomains + new_subdomains)

    def _load_ips(self):
        ips_file = os.path.join(self.user_config.user_dir, 'domains', "%s.ip_list" % self.domain_name)
        if os.path.exists(ips_file):
            new_ips = []

            with open(ips_file, 'r') as fd_ips_file:
                fcntl.flock(fd_ips_file, fcntl.LOCK_EX)

                for newip in fd_ips_file:
                    newip = newip.strip()
                    new_ips.append(newip)

            self.ips = uniq_list(self.ips + new_ips)

    def get_pointers(self):
        return self.pointers

    def get_subdomains(self):
        return self.subdomains

    def get_ips(self):
        return self.ips

    def get_config(self):
        return self.config


class DirectAdminUserConfig(object):
    """
    DirectAdmin user config
    """

    def __init__(self, user_dir):
        assert user_dir, "User dir must be specified"
        assert os.path.exists(user_dir), "User dir does not exists"

        self.user_dir = user_dir
        self.domains = {}
        self.user_name = os.path.basename(user_dir)

        self._load()

    def _load(self):
        domains_list = os.path.join(self.user_dir, 'domains.list')
        if os.path.exists(domains_list):

            with open(domains_list, 'r') as fd_domains_list:
                fcntl.flock(fd_domains_list, fcntl.LOCK_EX)

                for domain in fd_domains_list:
                    domain = domain.strip()
                    self.domains[domain] = DirectAdminUserDomain(self, domain)

    def get_domains(self):
        return self.domains.values()

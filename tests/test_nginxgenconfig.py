import os
import unittest
import shutil

from ..nginxvhostctl import NginxVhostsConfigManager
from ..nginxvhostctl import safe_create_path


class TestNginxGenConfigCommand(unittest.TestCase):
    DATA_DIR = 'data'
    USERS_CONFIG = os.path.join(DATA_DIR, 'users')
    OUT_CONFIG_DIR = os.path.join(DATA_DIR, 'testconf')

    def setUp(self):
        safe_create_path(self.OUT_CONFIG_DIR)

        source_tpl = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vhost_ssl.conf.tpl')
        shutil.copy(source_tpl, os.path.join(self.OUT_CONFIG_DIR, 'vhost_ssl.conf.tpl'))

    def tearDown(self):
        """
        Clean all after tests
        """
        if os.path.exists(self.OUT_CONFIG_DIR):
            shutil.rmtree(self.OUT_CONFIG_DIR, ignore_errors=True)

    def test_rebuild_all_users(self):
        conf_manager = NginxVhostsConfigManager(self.OUT_CONFIG_DIR, self.USERS_CONFIG)

        conf_manager.rebuild_all()

        self.assertEqual(0, len(conf_manager.map_subdomains.items))
        self.assertEqual(8, len(conf_manager.map_domains.items))
        self.assertEqual(8, len(conf_manager.map_users.items))
        self.assertTrue(os.path.exists(os.path.join(self.OUT_CONFIG_DIR, 'https_vhosts', 'dskfjhsdfsdfsdf.com.conf')))
        self.assertTrue(os.path.exists(os.path.join(self.OUT_CONFIG_DIR, 'https_vhosts', 'goandfly.ru.conf')))

        # test pointers
        self.assertEqual('"goandfly.ru"', conf_manager.map_domains.items['.00shop.ru'])
        self.assertEqual('"goandfly.ru"', conf_manager.map_domains.items['.goandfly.ru'])

    def test_rebuild_single_user(self):
        conf_manager = NginxVhostsConfigManager(self.OUT_CONFIG_DIR, self.USERS_CONFIG)

        conf_manager.delete_user('tstphpin')
        conf_manager.rebuild_user('tstphpin')

        self.assertEqual(0, len(conf_manager.map_subdomains.items))

        self.assertEqual(1, len(conf_manager.map_domains.items))
        self.assertEqual('"dskfjhsdfsdfsdf.com"', conf_manager.map_domains.items['.dskfjhsdfsdfsdf.com'])

        self.assertEqual(1, len(conf_manager.map_users.items))
        self.assertEqual('"tstphpin"', conf_manager.map_users.items['.dskfjhsdfsdfsdf.com'])

        self.assertTrue(os.path.exists(os.path.join(self.OUT_CONFIG_DIR, 'https_vhosts', 'dskfjhsdfsdfsdf.com.conf')))

import os
import unittest

from ..nginxlib import NginxMap


class TestNginxlibModule(unittest.TestCase):
    def tearDown(self):
        """
        Clean all after tests
        """
        if os.path.exists('test_map.test'):
            os.remove('test_map.test')

    def test_find_keys_by_value(self):
        map_object = self._create_test_map()

        self.assertEqual('.testhost2.ru', map_object.find_keys_by_value('"user2"').next())

    def test_file_locking(self):
        map_object = self._create_test_map()

        map_file = open('test_map.test', 'w')
        map_object._lock(map_file)

        # waiting for exception
        self.assertRaises(IOError, map_object.save, 'test_map.test')

    def test_load_from_file(self):
        map_object = self._create_test_map()

        map_object.save('test_map.test')

        # test the file format and contents
        file_lines = file('test_map.test', 'r')
        self.assertEqual('map $http_host $user {\n', file_lines.next())
        self.assertEqual('\thostnames;\n', file_lines.next())
        self.assertEqual('\tdefault                                      	"";\n', file_lines.next())
        self.assertEqual('\t.testhost1.ru                                \t"user1";\n', file_lines.next())
        self.assertEqual('\t.testhost2.ru                                \t"user2";\n', file_lines.next())
        self.assertEqual('\t.testhost3.ru                                \t"user3";\n', file_lines.next())
        self.assertEqual('\t.testhost4.ru                                \t"user4";\n', file_lines.next())
        self.assertEqual('\t.testhost5.ru                                \t"user5";\n', file_lines.next())
        self.assertEqual('}\n', file_lines.next())

        # load from file with wrong variables
        wrong_map = NginxMap.from_file('http_host', 'user1', 'test_map.test')
        self.assertEqual(0, len(wrong_map.items))

        # load map and test contents
        loaded_map = NginxMap.from_file('http_host', 'user', 'test_map.test')
        self.assertTrue(loaded_map.is_hostnames)
        self.assertEqual('http_host', loaded_map.map_key)
        self.assertEqual('user', loaded_map.map_variable)
        self.assertEqual('"user1"', loaded_map.items['.testhost1.ru'])
        self.assertEqual('"user2"', loaded_map.items['.testhost2.ru'])
        self.assertEqual('"user3"', loaded_map.items['.testhost3.ru'])
        self.assertEqual('"user4"', loaded_map.items['.testhost4.ru'])
        self.assertEqual('"user5"', loaded_map.items['.testhost5.ru'])

        # change and test map
        loaded_map.update_item('.testhost1.ru', '"user1ed"')
        loaded_map.update_item('.testhost3.ru', '"user3ed"')
        loaded_map.del_item('.testhost2.ru')
        loaded_map.save('test_map.test')

        loaded_map = NginxMap.from_file('http_host', 'user', 'test_map.test')
        self.assertTrue(loaded_map.is_hostnames)
        self.assertEqual('http_host', loaded_map.map_key)
        self.assertEqual('user', loaded_map.map_variable)
        self.assertEqual('"user1ed"', loaded_map.items['.testhost1.ru'])
        self.assertEqual(False, '.testhost2.ru' in loaded_map.items)
        self.assertEqual('"user3ed"', loaded_map.items['.testhost3.ru'])
        self.assertEqual('"user4"', loaded_map.items['.testhost4.ru'])
        self.assertEqual('"user5"', loaded_map.items['.testhost5.ru'])

    def _create_test_map(self):
        map_object = NginxMap('http_host', 'user')

        map_object.add_item('.testhost1.ru', '"user1"')
        map_object.add_item('.testhost2.ru', '"user2"')
        map_object.add_item('.testhost3.ru', '"user3"')
        map_object.add_item('.testhost4.ru', '"user4"')
        map_object.add_item('.testhost5.ru', '"user5"')

        return map_object

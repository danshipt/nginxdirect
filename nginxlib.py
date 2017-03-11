import errno
import fcntl
import os
import re
from time import sleep


class NginxMap:
    def __init__(self, map_key, map_variable):
        assert map_key, "Map section key must be specified"
        assert map_variable, "Map section variable must be specified"

        self.items = {}
        self.is_hostnames = True
        self.map_item_format = '\t%-45s\t%s;\n'
        self.section_key_pattern = r'\s+([^\s]+)\s+([^;]+)'
        self.map_key = map_key[1:] if map_key.startswith('$') else map_key
        self.map_variable = map_variable[1:] if map_variable.startswith('$') else map_variable

    def find_keys_by_value(self, value):
        for map_key in list(self.items):
            if self.items[map_key] == value:
                yield map_key

    def add_item(self, map_key, map_variable):
        assert map_key, "Map section key must be specified"
        assert map_variable, "Map section variable must be specified"

        if map_key in self.items:
            self.del_item(map_key)

        self.items[map_key] = map_variable

    def has_item(self, map_key):
        assert map_key, "Map section key must be specified"

        return map_key in self.items

    def del_item(self, map_key):
        assert map_key, "Map section key must be specified"

        if map_key not in self.items:
            raise Exception("Key %s does not exists" % map_key)

        if map_key in self.items:
            del self.items[map_key]

    def update_item(self, map_key, new_map_variable):
        assert map_key, "Map section key must be specified"

        if map_key not in self.items:
            raise Exception("Key %s does not exists" % map_key)

        if map_key in self.items:
            self.items[map_key] = new_map_variable

    def load(self, file_name):
        assert file_name, "File must be specified"
        assert os.path.exists(file_name), "Map file does not exists"

        section_header_pattern = r'map\s+\$%s\s+\$%s' % (self.map_key, self.map_variable)

        loading = False
        with open(file_name, 'r') as map_file:
            fcntl.flock(map_file, fcntl.LOCK_EX)
            for line in map_file:
                if loading:
                    if re.match(r'\s*map\s+', line):
                        break
                    match_object = re.match(self.section_key_pattern, line)
                    if match_object:
                        self.items[match_object.group(1)] = match_object.group(2)
                elif re.match(section_header_pattern, line):
                    loading = True
                    continue

        return loading  # return False if there is no such section

    def save(self, file_name):
        assert file_name, "File must be specified"

        with open(file_name, 'w') as map_file:
            self._lock(map_file, 30)

            map_file.write('map $%s $%s {\n' % (self.map_key, self.map_variable))

            if self.is_hostnames:
                map_file.write('\thostnames;\n')

            if 'default' in self.items:
                map_file.write(self.map_item_format % ('default', self.items['default']))
                del self.items['default']
            else:
                map_file.write(self.map_item_format % ('default', '""'))

            for item_key in sorted(self.items):
                map_file.write(self.map_item_format % (item_key, self.items[item_key]))

            map_file.write('}\n\n')

    def _lock(self, fd, timeout=10):
        assert fd

        retries = timeout
        while retries >= 0:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except IOError as e:
                if e.errno != errno.EAGAIN or e.errno != errno.EACCES:
                    retries -= 1
                    sleep(1)
                else:
                    raise e

        raise IOError("Can't acquire lock.")

    @staticmethod
    def from_file(map_key, map_variable, file_name):
        assert map_key, "Map section key must be specified"
        assert map_variable, "Map section variable must be specified"
        assert file_name, "File must be specified"
        assert os.path.exists(file_name), "Map file does not exists"

        section = NginxMap(map_key, map_variable)
        section.load(file_name)

        return section

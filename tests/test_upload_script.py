# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import errno
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import tempfile
import shutil
import re
import subprocess
import requests
import time
import random
from configparser import ConfigParser
from parameterized import parameterized

PY2 = sys.version_info.major == 2

# Path to the actual CGI script that should be tested
CGI_SCRIPT = os.path.join(os.path.dirname(__file__), '../src/web/upload.cgi')

# A snippet for creating the server in a temporary location. We need to write a
# separate script as it needs to run with working directory set to the
# temporary directory.
SERVER = """#!/usr/bin/env python
import BaseHTTPServer
import CGIHTTPServer
s = BaseHTTPServer.HTTPServer(('%s', %s), CGIHTTPServer.CGIHTTPRequestHandler)
s.handle_request()
"""

# MD5 hash of "hello.txt" and "new.txt" strings used in a few tests
HASH = '2e54144ba487ae25d03a3caba233da71'
NEW_HASH = 'fce67ea4590d3b789fff55a37271f29f'
SHA512 = 'acec329f80cc50edbab0dfbc2283d427ac673f84e6d8b949101791867b9b7771a53d2ffb1f8386189227beed4395b9a78171a1349700e2885c70ae14358d72ff'     # noqa
NEW_SHA512 = 'd3d67bc3e3848925892de9b132c9ff4054a05c9dbc7b4366d16b5c6b87c898df60da162e9ec415d4dc16470128ef52c11c44fc06da2841543ddeb351b10e9fb2' # noqa

# The first value is what will be sent in the request, the second is the full
# namespaced module name.
EXISTING_MODULES = [
    ("pkg", "rpms/pkg"),
    ("rpms/pkg", "rpms/pkg"),
    ("apbs/pkg", "apbs/pkg"),
]
NON_EXISTING_MODULES = [
    ("bad", "rpms/bad"),
    ("rpms/bad", "rpms/bad"),
    ("apbs/bad", "apbs/bad"),
]
OLD_FILE_MODULES = [
    ('old', 'rpms/old'),
    ('rpms/old', 'rpms/old'),
    ('apbs/old', 'apbs/old'),
]

GIT_DIR = 'srv/git'
CACHE_DIR = 'srv/cache/lookaside'


class UploadTest(unittest.TestCase):

    def setUp(self):
        self.hostname = 'localhost'
        self.port = random.randrange(59898, 65534)
        # Create temporary filesystem tree
        self.topdir = tempfile.mkdtemp()
        os.chmod(self.topdir, 0o0777)
        # Copy cgi script and tweak it with new path
        cgi = os.path.join(self.topdir, 'cgi-bin', 'upload.cgi')
        os.mkdir(os.path.join(self.topdir, 'cgi-bin'))
        _copy_tweak(CGI_SCRIPT, cgi, self.topdir)
        shutil.copystat(CGI_SCRIPT, cgi)
        # Generate temporary distgit config for this test run
        self.config = _dump_config_file(self.topdir)

        self._run_server()

        # Create a package with a single source file in each namespace
        for _, module in EXISTING_MODULES:
            self.setup_module(module)
            self.touch('%s/%s/hello.txt/md5/%s/hello.txt' % (CACHE_DIR, module, HASH))
            self.touch('%s/%s/hello.txt/sha512/%s/hello.txt' % (CACHE_DIR, module, SHA512))

        # These are modules with sources in old MD5 path only.
        for _, module in OLD_FILE_MODULES:
            self.setup_module(module)
            self.touch('%s/%s/hello.txt/%s/hello.txt' % (CACHE_DIR, module, HASH))

    def tearDown(self):
        shutil.rmtree(self.topdir)
        if not self.server.poll():
            # The server did not exit yet, so let's kill it.
            try:
                self.server.terminate()
            except OSError as exc:
                # It's possible for the server to exit before we try to kill
                # it. In that case we get ESRCH (No such process). This is
                # fine. All other exceptions should still be reported and fail
                # the tests.
                if exc.errno != errno.ESRCH:
                    raise
        self.server.wait()

    def _log_output(self):
        self.output.seek(0)
        print(self.output.read())

    def _run_server(self):
        """Start a server in a temporary directory, and capture its output."""
        script = os.path.join(self.topdir, 'server.py')
        with open(script, 'w') as f:
            f.write(SERVER % (self.hostname, self.port))
        os.chmod(script, 0o0755)
        self.output = tempfile.TemporaryFile()
        self.server = subprocess.Popen(script, cwd=self.topdir,
                                       stdout=self.output,
                                       stderr=subprocess.STDOUT,
                                       env={'SCRIPT_FILENAME': 'foo',
                                            'DISTGIT_CONFIG': self.config})
        time.sleep(0.1)     # Wait for server to be up.
        self.url = 'http://%s:%s/cgi-bin/upload.cgi' % (self.hostname, self.port)

    def upload(self, name, hash, hashtype='md5', filename=None, filepath=None, mtime=None):
        """Send a request to the CGI script. Exactly one of filename and
        filepath has to be provided.

        :param name: name of the module
        :param hash: hash of the file
        :param filename: name of a file to check
        :param filepath: path to a file to upload
        """
        args = {
            'name': name,
            '%ssum' % hashtype: hash,
        }
        if filename:
            args['filename'] = filename
        if mtime:
            args["mtime"] = mtime

        files = None
        if filepath:
            files = {'file': open(filepath, 'rb')}

        response = requests.post(self.url, data=args, files=files)
        self._log_output()
        self.assertEqual(response.status_code, 200)
        return response.text

    def touch(self, filename, contents=None):
        """Create a file in a given location and return its path."""
        contents = contents or filename
        path = os.path.join(self.topdir, filename)
        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass
        print('Creating %s' % path)
        with open(path, 'w') as f:
            f.write(contents)
        return path

    def setup_module(self, name):
        for path in [GIT_DIR + '/%s.git', CACHE_DIR + '/%s']:
            self.touch(os.path.join(self.topdir, path % name, '.keep'))

    def assertFileExists(self, module_name, filename, hash, mtime=None):
        path = os.path.join(self.topdir, CACHE_DIR, module_name, filename, hash, filename)
        self.assertTrue(os.path.exists(path), '%s should exist' % path)
        if mtime:
            self.assertEqual(os.stat(path).st_mtime, mtime)

    @parameterized.expand(EXISTING_MODULES + OLD_FILE_MODULES)
    def test_check_existing_file(self, module, ns_module):
        resp = self.upload(module, hash=HASH, filename='hello.txt')
        self.assertEqual(resp, 'Available\n')

    @parameterized.expand(EXISTING_MODULES)
    def test_check_existing_file_with_bad_hash(self, module, ns_module):
        resp = self.upload(module, hash='abc', filename='hello.txt')
        self.assertEqual(resp, 'Missing\n')

    @parameterized.expand(EXISTING_MODULES)
    def test_check_missing_file(self, module, ns_module):
        resp = self.upload(module, hash='abc', filename='foo.txt')
        self.assertEqual(resp, 'Missing\n')

    @parameterized.expand(EXISTING_MODULES)
    def test_upload_file(self, module, ns_module):
        test_file = self.touch('new.txt')
        resp = self.upload(module, hash=NEW_HASH, filepath=test_file)
        self.assertEqual(resp, 'File new.txt Size 7 STORED OK\n')
        self.assertFileExists(ns_module, 'new.txt', NEW_HASH)
        self.assertFileExists(ns_module, 'new.txt', 'md5/' + NEW_HASH)

    @parameterized.expand(EXISTING_MODULES)
    def test_upload_file_bad_checksum(self, module, ns_module):
        test_file = self.touch('hello.txt')
        resp = self.upload(module, hash='ABC', filepath=test_file)
        self.assertEqual(resp, 'MD5 check failed. Received %s instead of ABC\n' % HASH)

    @parameterized.expand(NON_EXISTING_MODULES)
    def test_upload_to_non_existing_module(self, module, ns_module):
        test_file = self.touch('hello.txt')
        resp = self.upload(module, hash=HASH, filepath=test_file)
        self.assertEqual(resp, "Module '%s' does not exist!\n" % ns_module)

    @parameterized.expand(EXISTING_MODULES)
    def test_rejects_unknown_hash(self, module, ns_module):
        test_file = self.touch('hello.txt')
        resp = self.upload(module, hash='deadbeef', hashtype='crc32', filepath=test_file)
        self.assertEqual(resp, "Required checksum is not present\n")

    @parameterized.expand(EXISTING_MODULES)
    def test_accepts_sha_512_hash(self, module, ns_module):
        test_file = self.touch('new.txt')
        resp = self.upload(module, hash=NEW_SHA512, hashtype='sha512', filepath=test_file)
        self.assertEqual(resp, 'File new.txt Size 7 STORED OK\n')
        self.assertFileExists(ns_module, 'new.txt', 'sha512/' + NEW_SHA512)

    @parameterized.expand(EXISTING_MODULES)
    def test_bad_sha512_hash(self, module, ns_module):
        test_file = self.touch('hello.txt')
        resp = self.upload(module, hash='ABC', hashtype='sha512', filepath=test_file)
        self.assertEqual(resp, 'SHA512 check failed. Received %s instead of ABC\n' % SHA512)

    @parameterized.expand(EXISTING_MODULES)
    def test_check_existing_sha512_correct(self, module, ns_module):
        resp = self.upload(module, hash=SHA512, hashtype='sha512', filename='hello.txt')
        self.assertEqual(resp, 'Available\n')

    @parameterized.expand(EXISTING_MODULES)
    def test_check_existing_sha512_mismatch(self, module, ns_module):
        resp = self.upload(module, hash='abc', hashtype='sha512', filename='hello.txt')
        self.assertEqual(resp, 'Missing\n')

    @parameterized.expand(EXISTING_MODULES)
    def test_upload_mtime(self, module, ns_module):
        test_file = self.touch('new.txt')
        resp = self.upload(module, hash=NEW_HASH, filepath=test_file, mtime="1234")
        self.assertFileExists(ns_module, 'new.txt', NEW_HASH, mtime=1234)

    @parameterized.expand(EXISTING_MODULES)
    def test_upload_invalid_mtime(self, module, ns_module):
        test_file = self.touch('new.txt')
        resp = self.upload(module, hash=NEW_HASH, filepath=test_file, mtime="abc")
        self.assertEqual(resp, "Invalid value sent for mtime 'abc'\n")


def _copy_tweak(source_file, dest_file, topdir):
    """Copy the script from source_file to dest_file, and tweak constants to
    point to topdir.
    """
    regex = re.compile(r'''^(GITREPO|CACHE_DIR)\s*=\s*['"]([^'"]+)['"]$''')
    with open(source_file) as source:
        with open(dest_file, 'w') as dest:
            for line in source:
                if PY2 and line == "#!/usr/bin/python3\n":
                    line = line.replace("python3", "python2")

                m = regex.match(line)
                if m:
                    line = "%s = '%s%s'\n" % (m.group(1), topdir, m.group(2))
                dest.write(line)

def _dump_config_file(topdir):
    config = ConfigParser()
    config["dist-git"] = {
        "git_author_name": "Fedora Release Engineering",
        "git_author_email": "rel-eng@lists.fedoraproject.org",
        "cache_dir": CACHE_DIR,
        "lookaside_dir": CACHE_DIR,
        "gitroot_dir": GIT_DIR,
        "gitolite": True,
        "grok": True,
        "default_namespace": "rpms",
    }

    config["upload"] = {
        "fedmsgs": False,
        "old_paths": True,
        "nomd5": False,
        "disable_group_check": True,
    }

    tmp = os.path.join(topdir, "dist-git-test.conf")
    with open(tmp, "w") as configfile:
        config.write(configfile)
    return tmp

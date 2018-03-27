#!/usr/bin/python
#
# CGI script to handle file updates for the rpms git repository. There
# is nothing really complex here other than tedious checking of our
# every step along the way...
#

import os
import sys
import errno
import cgi
import stat
import hashlib
import tempfile

# reading buffer size
BUFFER_SIZE = 4096
GITREPO = "/srv/git"
DEFAULT_NAMESPACE = 'rpms'

# Lookaside cache directory
CACHE_DIR = '/srv/cache/lookaside'

form = cgi.FieldStorage()
os.umask(002)

def log_msg(*msgs):
    sys.stderr.write(' '.join(map(str,msgs)) + '\n')

# abort running the script
def send_error(text):
    print "Content-type: text/plain\n"
    print text
    sys.exit(1)

# prepare to exit graciously
def send_ok(text):
    print "Content-Type: text/plain"
    print
    if text:
        print text

# check and validate that all the fields are present
def check_form(var, strip=True):
    if not form.has_key(var):
        send_error("required field '%s' is not present" % (var,))
    ret = form.getvalue(var)
    if type(ret) == type([]):
        send_error("Multiple values given for '%s'. Aborting" % (var,))
    if strip:
        ret = os.path.basename(ret) # this is a path component
    return ret


def hardlink(src, dst):
    """Create a hardlink, making sure the target directory exists."""
    makedirs(os.path.dirname(dst))
    if os.path.exists(dst):
        # The file already exists, let's hardlink over it.
        os.unlink(dst)
    os.link(src, dst)
    log_msg('ln %s %s' % (src, dst))


def makedirs(path, mode=0o2775):
    """Create a directory with all parents. If it already exists, then do
    nothing."""
    try:
        os.makedirs(path, mode=mode)
        log_msg('mkdir -p %s' % path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            send_error('Failed to create directory: %s' % exc)


def check_file_exists(path, filename, upload):
    """Send message if exists and exit the script."""
    if not os.access(path, os.F_OK | os.R_OK):
        # File does not exist, nothing to do here.
        return

    if upload is None:
        # File exists and we're just checking.
        message = "Available"
    else:
        # File exists and we wanted to upload it. Just say it's there already.
        upload.file.close()
        s = os.stat(path)
        message = "File %s already exists\nFile: %s Size: %d" % (
            filename, path, s[stat.ST_SIZE])
    send_ok(message)
    sys.exit(0)


# Get correct hashing algorithm
if 'sha512sum' in form:
    checksum = check_form('sha512sum')
    hash_type = 'sha512'
elif 'md5sum' in form:
    checksum = check_form('md5sum')
    hash_type = 'md5'
else:
    send_error('Required checksum is not present')


NAME = check_form("name", strip=False)

if '/' not in NAME:
    NAME = '%s/%s' % (DEFAULT_NAMESPACE, NAME)

# Is this a submission or a test?
FILE = None
FILENAME = None
if form.has_key("filename"):
    # check the presence of the file
    FILENAME = check_form("filename")
else:
    if form.has_key("file"):
        FILE = form["file"]
        if not FILE.file:
            send_error("No file given for upload. Aborting")
        try:
            FILENAME = os.path.basename(FILE.filename)
        except:
            send_error("Could not extract the filename for upload. Aborting")
    else:
        send_error("required field '%s' is not present" % ("file", ))

# Now that all the fields are valid,, figure out our operating environment
if not os.environ.has_key("SCRIPT_FILENAME"):
    send_error("My running environment is funky. Aborting")

# try to see if we already have this file...
file_dest = "%s/%s/%s/%s/%s/%s" % (CACHE_DIR, NAME, FILENAME, hash_type, checksum, FILENAME)
old_path = "%s/%s/%s/%s/%s" % (CACHE_DIR, NAME, FILENAME, checksum, FILENAME)

check_file_exists(file_dest, FILENAME, FILE)
if hash_type == 'md5':
    # If we're using MD5, handle the case of the file only existing in the old
    # path. Once the new checksum is fully deployed, this condition will become
    # obsolete.
    check_file_exists(old_path, FILENAME, FILE)

# just checking?
if FILE is None:
    send_ok("Missing")
    sys.exit(-9)

# if a directory exists, check that it has the proper permissions
def check_dir(tmpdir, wok=os.W_OK):
    if not os.access(tmpdir, os.F_OK):
        return 0
    if not os.access(tmpdir, os.R_OK|wok|os.X_OK):
        send_error("Unable to write to %s repository." % (
            tmpdir,))
    if not os.path.isdir(tmpdir):
        send_error("Path %s is not a directory." % (tmpdir,))
    return 1

if not os.environ.has_key("SCRIPT_FILENAME"):
    send_error("My running environment is funky. Aborting")
# the module's top level directory
my_moddir = "%s/%s" % (CACHE_DIR, NAME)
my_filedir = "%s/%s" % (my_moddir, FILENAME)
hash_dir = "%s/%s/%s" % (my_filedir, hash_type, checksum)

# first test if the module really exists
if not check_dir("%s/%s.git" % (GITREPO, NAME), 0):
    log_msg("Unknown module", NAME)
    send_ok("Module '%s' does not exist!" % (NAME,))
    sys.exit(-9)

makedirs(my_moddir)

# grab a temporary filename and dump our file in there
tempfile.tempdir = my_moddir
tmpfile = tempfile.mktemp(checksum)
tmpfd = open(tmpfile, "wb+")
# now read the whole file in
m = hashlib.new(hash_type)
FILELENGTH=0
while 1:
    s = FILE.file.read(BUFFER_SIZE)
    if not s:
        break
    tmpfd.write(s)
    m.update(s)
    FILELENGTH = FILELENGTH + len(s)
# now we're done reading, check the MD5 sum of what we got
tmpfd.close()
check_checksum = m.hexdigest()
if checksum != check_checksum:
    send_error("%s check failed. Received %s instead of %s" % (
        hash_type.upper(), check_checksum, checksum))
# wow, even the checksum matches. make sure full path is valid now
makedirs(hash_dir)
# and move our file to the final location
os.rename(tmpfile, file_dest)
log_msg("Stored %s (%s bytes)" % (file_dest, FILELENGTH))
send_ok("File %s Size %d STORED OK" % (FILENAME, FILELENGTH))

# The file was uploaded with MD5, so we hardlink it to the old location
# (without hash type). This is a temporary workaround to make sure old clients
# can access files they uploaded.
if hash_type == 'md5':
    hardlink(file_dest, old_path)

sys.exit(0)

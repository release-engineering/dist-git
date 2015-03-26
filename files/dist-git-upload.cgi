#!/usr/bin/python
#
# CGI script to handle file updates for the rpms git repository. There
# is nothing really complex here other than tedious checking of our
# every step along the way...
#
# License: GPL

import os
import sys
import cgi
import tempfile
import grp
import pwd
import syslog
import smtplib

import fedmsg
import fedmsg.config

from ConfigParser import ConfigParser

from email import Header, Utils
try:
    from email.mime.text import MIMEText
except ImportError:
    from email.MIMEText import MIMEText

import hashlib

# Reading buffer size
BUFFER_SIZE = 4096

# We check modules exist from this dircetory
GITREPO = '/var/lib/dist-git/git/rpms'

# Lookaside cache directory
CACHE_DIR = '/var/lib/dist-git/cache/lookaside/pkgs'

# Fedora Packager Group
PACKAGER_GROUP = 'packager'

# dist git configuration file
CONFIG_FILE = "/etc/dist-git/dist-git.conf"

def send_error(text):
    print text
    sys.exit(1)

def check_form(form, var):
    ret = form.getvalue(var, None)
    if ret is None:
        send_error('Required field "%s" is not present.' % var)
    if isinstance(ret, list):
        send_error('Multiple values given for "%s". Aborting.' % var)
    return ret

def check_auth(username):
    authenticated = False
    try:
        if username in grp.getgrnam(PACKAGER_GROUP)[3]:
            authenticated = True
    except KeyError:
        pass
    return authenticated

def send_email(pkg, checksum, filename, username, email_domain, owner_emails):
    text = """A file has been added to the lookaside cache for %(pkg)s:

%(checksum)s  %(filename)s""" % locals()
    msg = MIMEText(text)
    try:
        sender_name = pwd.getpwnam(username)[4]
        sender_email = "{username}@{domain}".format(username=username,
                                                    domain=email_domain)
    except KeyError:
        sender_name = ''
        sender_email = "nobody@{domain}".format(domain=email_domain)
        syslog.syslog('Unable to find account info for %s (uploading %s)' %
                      (username, filename))
    if sender_name:
        try:
            sender_name = unicode(sender_name, 'ascii')
        except UnicodeDecodeError:
            sender_name = Header.Header(sender_name, 'utf-8').encode()
            msg.set_charset('utf-8')
    sender = Utils.formataddr((sender_name, sender_email))

    recipients = owner_emails.replace("$PACKAGE", pkg).split(",")
    msg['Subject'] = 'File %s uploaded to lookaside cache by %s' % (
            filename, username)
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['X-Fedora-Upload'] = '%s, %s' % (pkg, filename)
    try:
        s = smtplib.SMTP('bastion')
        s.sendmail(sender, recipients, msg.as_string())
    except:
        syslog.syslog('sending mail for upload of %s failed!' % filename)

def _get_conf(cp, section, option, default):
    if cp.has_section(section) and cp.has_option(section, option):
        return cp.get(section, option)
    return default

def main():
    config = ConfigParser()
    config.read(CONFIG_FILE)

    EMAIL_DOMAIN = _get_conf(config, "notifications", "email_domain", "fedoraproject.org")
    PKG_OWNER_EMAILS = _get_conf(config, "notifications", "pkg_owner_emails",
                                 "$PACKAGE-owner@fedoraproject.org,scm-commits@lists.fedoraproject.org")

    os.umask(002)

    username = os.environ.get('SSL_CLIENT_S_DN_CN', None)
    if not check_auth(username):
        print 'Status: 403 Forbidden'
        print 'Content-type: text/plain'
        print
        print 'You must connect with a valid certificate and be in the %s group to upload.' % PACKAGER_GROUP
        sys.exit(0)

    print 'Content-Type: text/plain'
    print

    assert os.environ['REQUEST_URI'].split('/')[1] == 'repo'

    form = cgi.FieldStorage()
    name = check_form(form, 'name')

    # Search for the file hash, start with stronger hash functions
    if form.has_key('sha512sum'):
        checksum = check_form(form, 'sha512sum')
        hash_type = "sha512"

    elif form.has_key('md5sum'):
        # Fallback on md5, as it's what we currently use
        checksum = check_form(form, 'md5sum')
        hash_type = "md5"

    else:
        send_error('Required checksum is not present.')

    action = None
    upload_file = None
    filename = None

    # Is this a submission or a test?
    # in a test, we don't get a file, just a filename.
    # In a submission, we don;t get a filename, just the file.
    if form.has_key('filename'):
        action = 'check'
        filename = check_form(form, 'filename')
        filename = os.path.basename(filename)
        print >> sys.stderr, '[username=%s] Checking file status: NAME=%s FILENAME=%s %sSUM=%s' % (username, name, filename, hash_type.upper(), checksum)
    else:
        action = 'upload'
        if form.has_key('file'):
            upload_file = form['file']
            if not upload_file.file:
                send_error('No file given for upload. Aborting.')
            filename = os.path.basename(upload_file.filename)
        else:
            send_error('Required field "file" is not present.')
        print >> sys.stderr, '[username=%s] Processing upload request: NAME=%s FILENAME=%s %sSUM=%s' % (username, name, filename, hash_type.upper(), checksum)

    module_dir = os.path.join(CACHE_DIR, name)
    hash_dir = os.path.join(module_dir, filename, hash_type, checksum)
    msgpath = os.path.join(name, module_dir, filename, hash_type, checksum, filename)

    if hash_type == "md5":
        # Preserve compatibility with the current folder hierarchy for md5
        hash_dir = os.path.join(module_dir, filename, checksum)
        msgpath = os.path.join(name, module_dir, filename, checksum, filename)

    unwanted_prefix = '/var/lib/dist-git/cache/lookaside/pkgs/'
    if msgpath.startswith(unwanted_prefix):
        msgpath = msgpath[len(unwanted_prefix):]

    # first test if the module really exists
    git_dir = os.path.join(GITREPO, '%s.git' %  name)
    if not os.path.isdir(git_dir):
        print >> sys.stderr, '[username=%s] Unknown module: %s' % (username, name)
        send_error('Module "%s" does not exist!' % name)

    # try to see if we already have this file...
    dest_file = os.path.join(hash_dir, filename)
    if os.path.exists(dest_file):
        if action == 'check':
            print 'Available'
        else:
            upload_file.file.close()
            dest_file_stat = os.stat(dest_file)
            print 'File %s already exists' % filename
            print 'File: %s Size: %d' % (dest_file, dest_file_stat.st_size)
        sys.exit(0)
    elif action == 'check':
        print 'Missing'
        sys.exit(0)

    # check that all directories are in place
    if not os.path.isdir(module_dir):
        os.makedirs(module_dir, 02775)

    # grab a temporary filename and dump our file in there
    tempfile.tempdir = module_dir
    tmpfile = tempfile.mkstemp(checksum)[1]
    tmpfd = open(tmpfile, 'w')

    # now read the whole file in
    m = getattr(hashlib, hash_type)()
    filesize = 0
    while True:
        data = upload_file.file.read(BUFFER_SIZE)
        if not data:
            break
        tmpfd.write(data)
        m.update(data)
        filesize += len(data)

    # now we're done reading, check the checksum of what we got
    tmpfd.close()
    check_checksum = m.hexdigest()
    if checksum != check_checksum:
        os.unlink(tmpfile)
        send_error("%s check failed. Received %s instead of %s." % (hash_type.upper(), check_checksum, checksum))

    # wow, even the checksum matches. make sure full path is valid now
    if not os.path.isdir(hash_dir):
        os.makedirs(hash_dir, 02775)
        print >> sys.stderr, '[username=%s] mkdir %s' % (username, hash_dir)

    os.rename(tmpfile, dest_file)
    os.chmod(dest_file, 0644)

    print >> sys.stderr, '[username=%s] Stored %s (%d bytes)' % (username, dest_file, filesize)
    print 'File %s size %d %s %s stored OK' % (filename, filesize, hash_type.upper(), checksum)
    send_email(name, checksum, filename, username, EMAIL_DOMAIN, PKG_OWNER_EMAILS)

    # Emit a fedmsg message.  Load the config to talk to the fedmsg-relay.
    try:
        config = fedmsg.config.load_config([], None)
        config['active'] = True
        config['endpoints']['relay_inbound'] = config['relay_inbound']
        fedmsg.init(name="relay_inbound", cert_prefix="lookaside", **config)

        topic = "lookaside.new"
        msg = dict(name=name, md5sum=checksum, filename=filename.split('/')[-1],
                   agent=username, path=msgpath)
        fedmsg.publish(modname="git", topic=topic, msg=msg)
    except Exception as e:
        print "Error with fedmsg", str(e)

if __name__ == '__main__':
    main()

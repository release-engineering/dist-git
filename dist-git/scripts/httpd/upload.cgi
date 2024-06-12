#!/usr/bin/python3
#
# CGI script to handle file updates for the rpms git repository. There
# is nothing really complex here other than tedious checking of our
# every step along the way...
#
# License: GPL

import cgi
import errno
import grp
import hashlib
import os
import sys
import tempfile
import time

from configparser import ConfigParser

# Reading buffer size
BUFFER_SIZE = 4096

# Fedora Packager Group
PACKAGER_GROUP = 'packager'

# Path to a config file
CONFIG = os.environ.get('DISTGIT_CONFIG', '/etc/dist-git/dist-git.conf')


def send_error(text, status='500 Internal Server Error'):
    """Send an error back to the client

    This ensures that the client will get a proper error, including the HTTP
    status code, so that it can handle problems appropriately.

    Args:
        text (str): The error message to send the client
        status (str, optional): The HTTP status code to return to the client.
    """
    print('Status: %s' % status)
    print('Content-type: text/plain\n')
    print(text)

    sys.exit(0)


def send(text, exit=True):
    """Send a success message back to the client

    Args:
        text (str): The message to send the client
        exit (bool, optional): If we should exit immediatelly or not.
            Use this if you want to additionally print out more content
            into response.
    """
    print('Status: 200 OK')
    print('Content-type: text/plain\n')
    print(text)

    if exit:
        sys.exit(0)


def check_form(form, var):
    ret = form.getvalue(var, None)

    if ret is None:
        send_error('Required field "%s" is not present.' % var,
                   status='400 Bad Request')

    if isinstance(ret, list):
        send_error('Multiple values given for "%s". Aborting.' % var,
                   status='400 Bad Request')
    return ret


def check_group(username):
    authenticated = False

    try:
        if username in grp.getgrnam(PACKAGER_GROUP)[3]:
            authenticated = True
    except KeyError:
        pass

    return authenticated


def hardlink(src, dest, username):
    makedirs(os.path.dirname(dest), username)

    try:
        os.link(src, dest)
    except OSError as e:
        if e.errno != errno.EEXIST:
            send_error(str(e))

        # The file already existed at the dest path, hardlink over it
        os.unlink(dest)
        os.link(src, dest)

    sys.stderr.write("[username=%s] ln %s %s\n" % (username, src, dest))


def makedirs(dir_, username, mode=0o2755):
    try:
        os.makedirs(dir_, mode=mode)
        sys.stderr.write('[username=%s] mkdir %s\n' % (username, dir_))
    except OSError as e:
        if e.errno != errno.EEXIST:
            send_error(str(e))


def ensure_namespaced(name, namespace):
    if not namespace:
        return name

    name_parts = name.split('/')
    if len(name_parts) == 1:
        return os.path.join(namespace, name)

    return name


def get_checksum_and_hash_type(form):
    # Search for the file hash, start with stronger hash functions
    if 'sha512sum' in form:
        checksum = check_form(form, 'sha512sum')
        hash_type = "sha512"

    elif 'md5sum' in form:
        # Fallback on md5
        checksum = check_form(form, 'md5sum')
        hash_type = "md5"

    else:
        send_error('Required checksum is not present',
                   status='400 Bad Request')

    return checksum, hash_type


def emit_message(config, name, checksum, filename, username, msgpath):
    emit_fedmsg(config, name, checksum, filename, username, msgpath)
    emit_fedora_message(config, name, checksum, filename, username, msgpath)


def emit_fedmsg(config, name, checksum, filename, username, msgpath):
    # Emit a fedmsg message. Load the config to talk to the fedmsg-relay.
    if config.getboolean('upload', 'fedmsgs', fallback=True):
        try:
            import fedmsg
            import fedmsg.config

            config = fedmsg.config.load_config([], None)
            config['active'] = True
            config['endpoints']['relay_inbound'] = config['relay_inbound']
            fedmsg.init(name="relay_inbound", cert_prefix="lookaside", **config)

            topic = "lookaside.new"
            msg = dict(name=name, md5sum=checksum,
                       filename=filename.split('/')[-1], agent=username,
                       path=msgpath)
            fedmsg.publish(modname="git", topic=topic, msg=msg)
        except Exception as e:
            sys.stderr.write("Error with fedmsg", str(e))


def emit_fedora_message(config, name, checksum, filename, username, msgpath):
    # Emit a fedmsg-messaging message
    if not config.getboolean('upload', 'fedora_messaging', fallback=True):
        return
    try:
        import fedora_messaging.api
        import fedora_messaging.config
        import fedora_messaging.exceptions
    except ImportError:
        sys.stderr.write(
            "fedora-messaging must be installed for the notifications to work.")
        return

    try:
        if config['upload'].get('fedora_messaging_config'):
            fedora_messaging.config.conf.load_config(
                config['upload']['fedora_messaging_config'])

        message = dict(
            name=name,
            md5sum=checksum,
            filename=filename.split('/')[-1],
            agent=username,
            path=msgpath
        )

        msg = fedora_messaging.api.Message(
            topic="git.lookaside.new",
            body=message
        )
        fedora_messaging.api.publish(msg)
    except fedora_messaging.exceptions.PublishReturned as e:
        sys.stderr.write("Fedora Messaging broker rejected message %s: %s" % (msg.id, e))
    except fedora_messaging.exceptions.ConnectionException as e:
        sys.stderr.write("Error sending message %s: %s" % (msg.id, e))
    except Exception as e:
        sys.stderr.write("Error sending fedora-messaging message.")
        sys.stderr.write("ERROR: %s\n" % e)


def get_config():
    config = ConfigParser()
    config.read(CONFIG)
    return config


def main():
    form = cgi.FieldStorage()
    config = get_config()
    os.umask(0o002)

    username = os.environ.get('SSL_CLIENT_S_DN_CN', None)
    gssname = os.environ.get('GSS_NAME', os.environ.get('REMOTE_USER', None))
    if gssname and '@' in gssname and not username:
        username = gssname.partition('@')[0]

    if not config.getboolean('upload', 'disable_group_check', fallback=False) and\
            not check_group(username):
        send_error('You must connect with a valid certificate and be in the '
                   '%s group to upload.' % PACKAGER_GROUP,
                   status='403 Forbidden')

    assert os.environ['REQUEST_URI'].split('/')[1] == 'repo'

    name = check_form(form, 'name').strip('/')
    checksum, hash_type = get_checksum_and_hash_type(form)

    action = None
    upload_file = None
    filename = None

    # Is this a submission or a test?
    # in a test, we don't get a file, just a filename.
    # In a submission, we don't get a filename, just the file.
    if 'filename' in form:
        action = 'check'
        filename = check_form(form, 'filename')
        filename = os.path.basename(filename)
        sys.stderr.write('[username=%s] Checking file status: NAME=%s '
                         'FILENAME=%s %sSUM=%s\n' % (username, name, filename,
                                                     hash_type.upper(),
                                                     checksum))
    else:
        action = 'upload'
        if 'file' in form:
            upload_file = form['file']
            if not upload_file.file:
                send_error('No file given for upload. Aborting.',
                           status='400 Bad Request')
            filename = os.path.basename(upload_file.filename)
        else:
            send_error('Required field "file" is not present.',
                       status='400 Bad Request')

        sys.stderr.write('[username=%s] Processing upload request: '
                         'NAME=%s FILENAME=%s %sSUM=%s\n' % (
                             username, name, filename, hash_type.upper(),
                             checksum))

    # prefix name by default namespace if configured
    if config['dist-git'].get('default_namespace'):
        name = ensure_namespaced(name, config['dist-git'].get('default_namespace')).strip('/')

    if config['dist-git'].get('lookaside_dir'):
        module_dir = os.path.join(config['dist-git']['lookaside_dir'], name)
    elif config['dist-git'].get('cache_dir'): # deprecated
        module_dir = os.path.join(config['dist-git']['cache_dir'], 'lookaside/pkgs', name)
    else:
        raise Exception('Please, set lookaside_dir config option.')

    hash_dir = os.path.join(module_dir, filename, hash_type, checksum)
    msgpath = os.path.join(name, filename, hash_type, checksum, filename)

    # first test if the module really exists
    git_dir = os.path.join(config['dist-git']['gitroot_dir'], '%s.git' % name)
    if not os.path.isdir(git_dir):
        sys.stderr.write('[username=%s] Unknown module: %s' % (username, name))
        send_error('Module "%s" does not exist!' % name,
                   status='404 Not Found')

    # try to see if we already have this file...
    dest_file = os.path.join(hash_dir, filename)
    old_dir = os.path.join(module_dir, filename, checksum)
    old_path = os.path.join(old_dir, filename)

    if os.path.exists(dest_file):
        if action == 'check':
            send('Available')
        else:
            upload_file.file.close()
            dest_file_stat = os.stat(dest_file)
            msg = 'File %s already exists\n' % filename
            msg += 'File: %s Size: %d' % (dest_file, dest_file_stat.st_size)
            send(msg)

    elif action == 'check':
        if os.path.exists(old_path):
            # The file had been uploaded at the old path
            hardlink(old_path, dest_file, username)
            send('Available')
        else:
            send('Missing')

    elif hash_type == "md5" and config.getboolean('upload', 'nomd5', fallback=True):
        send_error('Uploads with md5 are no longer allowed.',
                   status='406 Not Acceptable')

    # check that all directories are in place
    makedirs(module_dir, username)

    # grab a temporary filename and dump our file in there
    tempfile.tempdir = module_dir
    tmpfile = tempfile.mkstemp(checksum)[1]
    tmpfd = open(tmpfile, 'wb')

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
        send_error("%s check failed. Received %s instead of %s." %
                   (hash_type.upper(), check_checksum, checksum),
                   status='400 Bad Request')

    # wow, even the checksum matches. make sure full path is valid now
    makedirs(hash_dir, username)
    os.rename(tmpfile, dest_file)
    os.chmod(dest_file, 0o644)

    # set mtime of the uploaded file if provided
    if 'mtime' in form:
        mtime_str = form.getvalue('mtime')
        try:
            mtime = float(mtime_str)
        except ValueError:
            send_error('Invalid value sent for mtime "%s". Aborting.' % mtime_str,
                       status='400 Bad Request')

        os.utime(dest_file, (time.time(), mtime))

    sys.stderr.write('[username=%s] Stored %s (%d bytes)' % (username,
                                                             dest_file,
                                                             filesize))
    send('File %s size %d %s %s stored OK' % (filename, filesize,
                                              hash_type.upper(), checksum), exit=False)

    # Add the file to the old path, where fedpkg used to look for
    if hash_type == "md5" and config.getboolean('upload', 'old_paths', fallback=True):
        hardlink(dest_file, old_path, username)

    emit_message(config, name, checksum, filename, username, msgpath)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        sys.stderr.write('%s\n' % traceback.format_exc())
        send_error(str(e))

import os
import sys
import grp
import errno


# Fedora Packager Group
PACKAGER_GROUP = 'packager'


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

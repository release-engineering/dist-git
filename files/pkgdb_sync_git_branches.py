#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


This script is able to query pkgdb and retrieve for all packages which active
branches should be there, browse all the git repos and find out which active
branches are missing.

It even goes one step further but actually adjusting the git repo by adding
the missing branches (or even the missing repo)

"""

import multiprocessing.pool
import os
import subprocess
import time
import pipes

import requests
from ConfigParser import ConfigParser

# Do some off-the-bat configuration of fedmsg.
#   1) since this is a one-off script and not a daemon, it needs to connect
#      to the fedmsg-relay process running on another node (or noone will
#      hear it)
#   2) its going to use the 'shell' certificate which only 'sysadmin' has
#      read access to.  Contrast that with the 'scm' certificate which
#      everyone in the 'packager' group has access to.

def _get_conf(cp, section, option, default):
    if cp.has_section(section) and cp.has_option(section, option):
        return cp.get(section, option)
    return default

config = ConfigParser()
config.read("/etc/dist-git/dist-git.conf")
PKGDB_URL = _get_conf(config, "acls", "pkgdb_acls_url", "")
EMAIL_DOMAIN = _get_conf(config, "notifications", "email_domain", "fedoraproject.org")
PKG_OWNER_EMAILS = _get_conf(config, "notifications", "pkg_owner_emails",
                             "$PACKAGE-owner@fedoraproject.org,scm-commits@lists.fedoraproject.org")
DEFAULT_BRANCH_AUTHOR = _get_conf(config, "git", "default_branch_author",
                             "Fedora Release Engineering <rel-eng@lists.fedoraproject.org>")


GIT_FOLDER = '/var/lib/dist-git/git/rpms/'
MKBRANCH = '/usr/share/dist-git/mkbranch'
SETUP_PACKAGE = '/usr/share/dist-git/setup_git_package'

THREADS = 20
VERBOSE = False


class InternalError(Exception):
    pass


class ProcessError(InternalError):
    pass


def _invoke(program, args, cwd=None):
    '''Run a command and raise an exception if an error occurred.

    :arg program: The program to invoke
    :args: List of arguments to pass to the program

    raises ProcessError if there's a problem.
    '''
    cmdLine = [program]
    cmdLine.extend(args)
    if VERBOSE:
        print ' '.join(cmdLine)
        print '  in', cwd

    program = subprocess.Popen(
        cmdLine, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd)

    stdout, stderr = program.communicate()

    if program.returncode != 0:
        e = ProcessError()
        e.returnCode = program.returncode
        e.cmd = ' '.join(cmdLine)
        e.cwd = cwd
        e.message = 'Error, "%s" (in %r) returned %s\n  stdout: %s\n  stderr: %s' % (
            e.cmd, e.cwd, e.returnCode, stdout, stderr)
        print e.message
        raise e

    return stdout.strip()


def _create_branch(pkgname, branch, existing_branches):
    '''Create a specific branch for a package.

    :arg pkgname: Name of the package to branch
    :arg branch: Name of the branch to create
    :arg existing_branches: A list of the branches that already exist locally.

    '''
    branch = branch.replace('*', '').strip()
    if branch == 'master':
        print 'ERROR: Proudly refusing to create master branch. Invalid repo?'
        print 'INFO: Please check %s repo' % pkgname
        return

    if branch in existing_branches:
       print 'ERROR: Refusing to create a branch %s that exists' % branch
       return

    try:
        _invoke(MKBRANCH, ["--default-branch-author", pipes.quote(DEFAULT_BRANCH_AUTHOR),
                           branch, pkgname])
    except ProcessError, e:
        if e.returnCode == 255:
            # This is a warning, not an error
            return
        raise


def pkgdb_pkg_branch():
    """ Queries pkgdb information about VCS and return a dictionnary of
    which branches are available for which packages.

    :return: a dict[pkg_name] = [pkg_branches]
    :rtype: dict
    """
    data = requests.get(PKGDB_URL).json()

    output = {}
    for pkg in data['packageAcls']:
        if pkg in output:
            if VERBOSE:
                print 'Strange package: %s, it is present twice in the ' \
                    'pkgdb output' % pkg
            output[pkg].updated(data['packageAcls'][pkg].keys())
        else:
            output[pkg] = set(data['packageAcls'][pkg].keys())

    return output


def get_git_branch(pkg):
    """ For the specified package name, check the local git and return the
    list of branches found.
    """
    git_folder = os.path.join(GIT_FOLDER, '%s.git' % pkg)
    if not os.path.exists(git_folder):
        if VERBOSE:
            print 'Could not find %s' % git_folder
        return set()

    branches = [
       lclbranch.replace('*', '').strip()
       for lclbranch in _invoke('git', ['branch'], cwd=git_folder).split('\n')
    ]
    return set(branches)


def branch_package(pkgname, requested_branches, existing_branches):
    '''Create all the branches that are listed in the pkgdb for a package.

    :arg pkgname: The package to create branches for
    :arg requested_branches: The branches to creates
    :arg existing_branches: A list of existing local branches

    '''
    if VERBOSE:
        print 'Fixing package %s for branches %s' % (pkgname, requested_branches)

    # Create the devel branch if necessary
    exists = os.path.exists(os.path.join(GIT_FOLDER, '%s.git' % pkgname))
    if not exists or 'master' not in existing_branches:
        emails = PKG_OWNER_EMAILS.replace("$PACKAGE", pkgname)
        _invoke(SETUP_PACKAGE, ["--pkg-owner-emails", pipes.quote(emails),
                                "--email-domain", pipes.quote(EMAIL_DOMAIN),
                                "--default-branch-author", pipes.quote(DEFAULT_BRANCH_AUTHOR),
                                pkgname])
        if 'master' in requested_branches:
            requested_branches.remove('master')  # SETUP_PACKAGE creates master

    # Create all the required branches for the package
    # Use the translated branch name until pkgdb falls inline
    for branch in requested_branches:
        _create_branch(pkgname, branch, existing_branches)


def main():
    """ For each package found via pkgdb, check the local git for its
    branches and fix inconsistencies.
    """

    local_pkgs = set(os.listdir(GIT_FOLDER))
    local_pkgs = set([it.replace('.git', '') for it in local_pkgs])
    if VERBOSE:
        print "Found %i local packages" % len(local_pkgs)

    pkgdb_info = pkgdb_pkg_branch()

    pkgdb_pkgs = set(pkgdb_info.keys())
    if VERBOSE:
        print "Found %i pkgdb packages" % len(pkgdb_pkgs)

    ## Commented out as we keep the git of retired packages while they won't
    ## show up in the information retrieved from pkgdb.

    #if (local_pkgs - pkgdb_pkgs):
        #print 'Some packages are present locally but not on pkgdb:'
        #print ', '.join(sorted(local_pkgs - pkgdb_pkgs))

    if (pkgdb_pkgs - local_pkgs):
        print 'Some packages are present in pkgdb but not locally:'
        print ', '.join(sorted(pkgdb_pkgs - local_pkgs))


    if VERBOSE:
        print "Finding the lists of local branches for local repos."
    start = time.time()
    if THREADS == 1:
        git_branch_lookup = map(get_git_branch, sorted(pkgdb_info))
    else:
        threadpool = multiprocessing.pool.ThreadPool(processes=THREADS)
        git_branch_lookup = threadpool.map(get_git_branch, sorted(pkgdb_info))

    # Zip that list of results up into a lookup dict.
    git_branch_lookup = dict(zip(sorted(pkgdb_info), git_branch_lookup))

    if VERBOSE:
        print "Found all local git branches in %0.2fs" % (time.time() - start)

    tofix = set()
    for pkg in sorted(pkgdb_info):
        pkgdb_branches = pkgdb_info[pkg]
        git_branches = git_branch_lookup[pkg]
        diff = (pkgdb_branches - git_branches)
        if diff:
            print '%s missing: %s' % (pkg, ','.join(sorted(diff)))
            tofix.add(pkg)
            branch_package(pkg, diff, git_branches)

    if tofix:
        print 'Packages fixed (%s): %s' % (
            len(tofix), ', '.join(sorted(tofix)))
    else:
        if VERBOSE:
            print 'Didn\'t find any packages to fix.'


if __name__ == '__main__':
    import sys
    sys.exit(main())

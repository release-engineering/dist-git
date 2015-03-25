#!/usr/bin/python -t
#
# Create an /etc/gitolog/conf/getolog.conf file with acls for dist-git
#
# Takes no arguments!
#

import grp
import sys

import requests
from ConfigParser import ConfigParser

def _get_conf(cp, section, option, default):
    if cp.has_section(section) and cp.has_option(section, option):
        return cp.get(section, option)
    return default


if __name__ == '__main__':
    config = ConfigParser()
    config.read("/etc/dist-git/dist-git.conf")

    user_groups = _get_conf(config, "acls", "user_groups", "").split(",")
    admin_groups = _get_conf(config, "acls", "admin_groups", "").split(",")
    ACTIVE = _get_conf(config, "acls", "active_branches", "").split(",")
    RESERVED = _get_conf(config, "acls", "reserved_branches", "").split(",")
    pkgdb_acls_url = _get_conf(config, "acls", "pkgdb_acls_url", "")
    pkgdb_groups_url = _get_conf(config, "acls", "pkgdb_groups_url", "")


    # Read the ACL information from the packageDB
    data = requests.get(pkgdb_acls_url).json()

    # Get a list of all the packages
    acls = data['packageAcls']
    pkglist = data['packageAcls'].keys()
    pkglist.sort()

    # sanity check
    #if len(pkglist) < 2500:
    #    sys.exit(1)

    # get the list of all groups
    pkgdb_groups = requests.get(pkgdb_groups_url).json()

    # print out our user groups
    for group in user_groups + pkgdb_groups["groups"]:
        print "@{0} = {1}".format(group, " ".join(grp.getgrnam(group)[3]))


    # Give a little space before moving onto the permissions
    print ''
    # print our default permissions
    print 'repo @all'
    print '    -   VREF/update-block-push-origin = @all'
    if admin_groups:
        print '    RWC = @{}'.format(" @".join(admin_groups))
    print '    R = @all'
    #print '    RW  private-     = @all'
    # dont' enable the above until we prevent building for real from private-

    for pkg in pkglist:
        branchAcls = {} # Check whether we need to set separate per branch acls
        buffer = [] # Buffer the output per package
        masters = [] # Folks that have commit to master
        writers = [] # Anybody that has write access

        # Examine each branch in the package
        branches = acls[pkg].keys()
        branches.sort()
        for branch in branches:
            if not branch in ACTIVE:
                continue
            if 'packager' in acls[pkg][branch]['commit']['groups']:
                # If the packager group is defined, everyone has access
                buffer.append('    RWC   %s = @all' % (branch))
                branchAcls.setdefault('@all', []).append((pkg, branch))
                if branch == 'master':
                    masters.append('@all')
                if '@all' not in writers:
                    writers.append('@all')
            else:
                # Extract the owners
                committers = []
                owners = acls[pkg][branch]['commit']['people']
                owners.sort()
                for owner in owners:
                    committers.append(owner)
                for group in acls[pkg][branch]['commit']['groups']:
                    committers.append('@%s' % group)
                if branch == 'master':
                    masters.extend(committers)

                # add all the committers to the top writers list
                for committer in committers:
                    if not committer in writers:
                        writers.append(committer)

                # Print the committers to the acl for this package-branch
                committers = ' '.join(committers)
                buffer.append('    RWC   %s = %s' %
                              (branch, committers))
                branchAcls.setdefault(committers, []).append((pkg, branch))

        print
        print 'repo %s' % pkg
        #if len(branchAcls.keys()) == 1:
        #    acl = branchAcls.keys()[0]
        #    print '    RW               = %s' % acl
        #else:
        print '\n'.join(buffer)
        for reserved in RESERVED:
            print '    -    %s = @all' % reserved
        print '    RWC  refs/tags/ = %s' % ' '.join(writers)
        if masters:
            print '    RWC      = %s' % ' '.join(masters)
    sys.exit(0)

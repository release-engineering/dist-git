#!/bin/bash
#
# Create a new repo.
# THIS HAS TO BE RUN ON THE GIT SERVER!

# WARNING:
# This file is maintained within ansible
# All local changes will be lost.



# Figure out the environment we're running in
GITROOT=/var/lib/dist-git/git/rpms

# check if a moron is driving me
if [ ! -d $GITROOT ] ; then
    # we're not on the git server (this check is fragile)
    echo "ERROR: This script has to be run on the git server."
    echo "ERROR: Homer sez 'Duh'."
    exit -9
fi

# Local variables
VERBOSE=0
TEST=
IGNORE=
GIT_SSH_URL="ssh://localhost"

Usage() {
    cat <<EOF
Usage:
    $0 [OPTIONS] <package_name>

    Creates a new repo for <package_name>

Options:
    -h,--help			This help message
    --email-domain DOMAIN       Email domain for git hooks.maildomain
    --pkg-owner-emails EMAILS   Comma separated list of emails for
                                git hooks.mailinglist
EOF
}

# fail with no arguments
if [ $# -eq 0 ]; then
    Usage
    exit -1
fi

OPTS=$(getopt -o h -l help -l email-domain: -l pkg-owner-emails: -l default-branch-author: -- "$@")
if [ $? != 0 ]
then
    exit 1
fi

eval set -- "$OPTS"

while true ; do
    case "$1" in
        -h | --help) Usage; exit 0;;
        --email-domain) EMAIL_DOMAIN=$2; shift 2;;
        --pkg-owner-emails) PKG_OWNER_EMAILS=$2; shift 2;;
        --default-branch-author) AUTHOR=$2; shift 2;;
        --) shift; break;;
    esac
done

# fail when more or none packages are specified
if ! [ $# -eq 1 ]; then
    Usage
    exit -1
fi

PACKAGE=$1

if [ -z $EMAIL_DOMAIN ]; then
    EMAIL_DOMAIN=fedoraproject.org
fi

if [ -z $PKG_OWNER_EMAILS ]; then
    PKG_OWNER_EMAILS=$PACKAGE-owner@fedoraproject.org,scm-commits@lists.fedoraproject.org
fi

if [ -z $AUTHOR ]; then
    AUTHOR=`crudini --get /etc/dist-git/dist-git.conf git default_branch_author`
fi

# Sanity checks before we start doing damage
[ $VERBOSE -gt 1 ] && echo "Checking package $PACKAGE..."
if [ -f $GITROOT/$PACKAGE.git/refs/heads/master ] ; then
    echo "ERROR: Package module $PACKAGE already exists!" >&2
    exit -1
fi

# A cleanup in case gitolite came by this repo
if [ -f $GITROOT/$PACKAGE.git/hooks/update ] ; then
    echo "Gitolite already initialized this repo. Will remove its hooks"
    rm -f $GITROOT/$PACKAGE.git/hooks/update
fi

# "global" permissions check
if [ ! -w $GITROOT ] ; then
    echo "ERROR: You can not write to $GITROOT"
    echo "ERROR: You can not create repos"
    exit -1
fi

# Now start working on creating those branches
# Create a tmpdir to do some git work in
TMPDIR=$(mktemp -d /tmp/tmpXXXXXX)

# First create the master repo
mkdir -p $GITROOT/$PACKAGE.git
pushd $GITROOT/$PACKAGE.git >/dev/null
git init -q --shared --bare
echo "$PACKAGE" > description # This is used to figure out who to send mail to.
git config --add hooks.mailinglist $PKG_OWNER_EMAILS
git config --add hooks.maildomain $EMAIL_DOMAIN
popd >/dev/null

# Now clone that repo and create the .gitignore and sources file
git init -q $TMPDIR/$PACKAGE
pushd $TMPDIR/$PACKAGE >/dev/null
touch .gitignore sources
git add .
git commit -q -m 'Initial setup of the repo' --author "$AUTHOR"
git remote add origin $GITROOT/$PACKAGE.git
git push -q origin master
popd >/dev/null

# Place the gitolite update hook in place since we're not using our own
ln -s /var/lib/dist-git/gitolite/hooks/common/update $GITROOT/$PACKAGE.git/hooks/update


# Setup our post-receive hooks
mkdir -p $GITROOT/$PACKAGE.git/hooks/post-receive-chained.d
ln -s /usr/share/git-core/mail-hooks/gnome-post-receive-email \
    $GITROOT/$PACKAGE.git/hooks/post-receive-chained.d/post-receive-email
ln -s /usr/share/git-core/post-receive-fedmsg \
    $GITROOT/$PACKAGE.git/hooks/post-receive-chained.d/post-receive-fedmsg

# This one kicks off all the others in post-receive-chained.d
ln -s /usr/share/git-core/post-receive-chained \
    $GITROOT/$PACKAGE.git/hooks/post-receive

rm -rf $TMPDIR
echo "Done."

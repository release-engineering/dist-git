#!/bin/sh

python /usr/local/bin/pkgdb_sync_git_branches.py

TEMPDIR=`mktemp -d -p /var/tmp genacls.XXXXX`
export GL_BINDIR=/usr/bin

cd $TEMPDIR
# Only replace the acls if genacls completes successfully
if /usr/local/bin/genacls.pkgdb > gitolite.conf ; then
    mv gitolite.conf /etc/gitolite/conf/
    chown gen-acls:gen-acls -R /etc/gitolite/conf/
    HOME=/srv/git /usr/bin/gitolite compile
fi
cd /
rm -rf $TEMPDIR
chown root:packager /etc/gitolite/conf/gitolite.conf-compiled.pm
chmod g+r /etc/gitolite/conf/gitolite.conf-compiled.pm

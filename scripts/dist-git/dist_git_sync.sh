#!/bin/sh

python /usr/share/dist-git/pkgdb_sync_git_branches.py

TEMPDIR=`mktemp -d -p /var/tmp genacls.XXXXX`
export GL_BINDIR=/usr/bin

cd $TEMPDIR
# Only replace the acls if genacls completes successfully
if /usr/share/dist-git/pkgdb_gen_gitolite_conf.py > gitolite.conf ; then
    mv gitolite.conf /var/lib/dist-git/gitolite/conf/
    chown gen-acls:gen-acls -R /var/lib/dist-git/gitolite/conf/
    HOME=/var/lib/dist-git/git /usr/bin/gitolite compile
fi
cd /
rm -rf $TEMPDIR
chown root:packager /var/lib/dist-git/gitolite/conf/gitolite.conf-compiled.pm
chmod g+r /var/lib/dist-git/gitolite/conf/gitolite.conf-compiled.pm

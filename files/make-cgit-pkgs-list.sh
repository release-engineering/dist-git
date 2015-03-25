#!/bin/sh

#
# This simple script lists out the current pkgs git repos to a file. 
# This speeds up cgit as it doesn't have to recurse into all dirs 
# Looking for git repos. 
#
newfile=`mktemp`

cd /srv/git/rpms
ls > $newfile
mv -Z $newfile /srv/git/pkgs-git-repos-list
chown apache:apache /srv/git/pkgs-git-repos-list
chmod 644 /srv/git/pkgs-git-repos-list

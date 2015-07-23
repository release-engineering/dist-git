#!/bin/sh

#
# This simple script lists out the current pkgs git repos to a file. 
# This speeds up cgit as it doesn't have to recurse into all dirs 
# Looking for git repos. 
#
newfile=`mktemp`

cd /var/lib/dist-git/git/rpms
ls > $newfile
cp -fZ $newfile /var/lib/dist-git/git/pkgs-git-repos-list
rm $newfile
#chown apache:apache /var/lib/dist-git/git/pkgs-git-repos-list
chmod 644 /var/lib/dist-git/git/pkgs-git-repos-list

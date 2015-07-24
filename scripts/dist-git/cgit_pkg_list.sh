#!/bin/sh

#
# This simple script lists out the current pkgs git repos to a file. 
# This speeds up cgit as it doesn't have to recurse into all dirs 
# Looking for git repos. 
#

destination=/var/lib/dist-git/git/pkgs-git-repos-list

if [ -n "$1" ]
then
  destination=$1
fi

newfile=`mktemp`

cd /var/lib/dist-git/git/rpms
ls > $newfile
cp -fZ $newfile $destination
rm $newfile
#chown apache:apache $destination
chmod 644 $destination

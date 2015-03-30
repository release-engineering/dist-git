#!/bin/sh


# Bad, bad, bad developer! (Just temporary)
setenforce permissive
systemctl stop firewalld


### ENV ###
DISTGITHOME="/var/lib/dist-git/git/"
cd /home/adam
### COMMON CONFIG ###

echo ACTION: configuration
mkdir /etc/dist-git/
chmod 0755 /etc/dist-git/
cp files/dist_git_main.conf /etc/dist-git/dist-git.conf
chmod 0755 /etc/dist-git/dist-git.conf

echo ACTION: install all the packages:
yum install -y git httpd gitolite3 cgit perl-Sys-Syslog git-daemon python-requests /usr/sbin/semanage

echo ACTION: httpd config dir:
cp files/dist-git.conf /etc/httpd/conf.d/dist-git.conf
mkdir /etc/httpd/conf.d/dist-git

# echo ACTION: install the mod_ssl config:
# echo "LoadModule ssl_module modules/mod_ssl.so" > /etc/httpd/conf.d/ssl.conf

echo ACTION: SELinux httpd_use_nfs
# this is not important for the basic setup
setsebool -P httpd_use_nfs true

### DIST GIT ###

echo ACTION: root directory
mkdir -p $DISTGITHOME/rpms
chmod 0755 $DISTGITHOME
groupadd packager
chown :packager $DISTGITHOME/rpms
chmod 2775 $DISTGITHOME/rpms

echo ACTION: selinux context
semanage fcontext -a -t httpd_git_content_t "/var/lib/dist-git/git(/.*)?"
restorecon -R /var/lib/dist-git/git/

echo ACTION: dist git script dir
mkdir /usr/share/dist-git
chmod 755 /usr/share/dist-git

echo ACTION: dist git scripts
for SCRIPT in git_package.sh git_branch.sh pkgdb2-clone pkgdb_sync_git_branches.py
do
    cp files/scripts/$SCRIPT /usr/share/dist-git/
    chown root:root /usr/share/dist-git/$SCRIPT
    chmod 0755 /usr/share/dist-git/$SCRIPT
done

echo ACTION: httpd config for dist git
cp files/git-smart-http.conf /etc/httpd/conf.d/dist-git/

echo ACTION: cron job pkgdb_pkgdb_sync_git_branches
# tbd


### GITOLITE ###

echo ACTION: gen-acls group and user
groupadd gen-acls
useradd -g gen-acls -G packager -s /bin/bash -d $DISTGITHOME gen-acls

echo ACTION: directories
mkdir /var/log/gitolite
chown root:packager /var/log/gitolite
chmod 2775 /var/log/gitolite

mkdir -p /etc/gitolite/conf
chown gen-acls:gen-acls /etc/gitolite/conf
chmod 0755 /etc/gitolite/conf

mkdir /etc/gitolite/logs
chown gen-acls:packager /etc/gitolite/logs
chmod 0775 /etc/gitolite/logs

mkdir -p /etc/gitolite/local/VREF
chown gen-acls:packager /etc/gitolite/local/VREF 
chmod 0775 /etc/gitolite/local/VREF 

echo ACTION: gitolite config
cp files/gitolite.rc /etc/gitolite/
chmod 0755 /etc/gitolite/gitolite.rc

echo ACTION: repositories symlink
ln -s $DISTGITHOME/rpms/ $DISTGITHOME/repositories

echo ACTION: gitolite.rc symlink
ln -s /etc/gitolite/gitolite.rc $DISTGITHOME/.gitolite.rc

echo ACTION: gitolite config symlink
ln -s /etc/gitolite/ $DISTGITHOME/.gitolite

echo ACTION: update-block-push-origin symlink
ln -s /usr/share/git-core/update-block-push-origin /etc/gitolite/local/VREF/update-block-push-origin

echo ACTION: dist_git_sync.sh script
cp files/scripts/dist_git_sync.sh /usr/share/dist-git/
chmod 0755 /usr/share/dist-git/dist_git_sync.sh

echo ACTION: pkgdb_gen_gitolite_conf.py script
cp files/scripts/pkgdb_gen_gitolite_conf.py /usr/share/dist-git/
chmod 0755 /usr/share/dist-git/pkgdb_gen_gitolite_conf.py

echo ACTION: genacl daily cron job
# tbd

echo ACTION: admin users
echo "adam" > /etc/gitolite/admins
chown gen-acls:packager /etc/gitolite/admins
chmod 0660 /etc/gitolite/admins

echo ACTION: Fix permissions on the Gitolite stuff
mkdir /etc/gitolite/hooks
chown :packager /etc/gitolite/hooks
chmod 0770 /etc/gitolite/hooks

mkdir /etc/gitolite/hooks/common
chown :packager /etc/gitolite/hooks/common
chmod 0770 /etc/gitolite/hooks/common

touch /etc/gitolite/hooks/common/update
chown :packager /etc/gitolite/hooks/common/update
chmod 0755 /etc/gitolite/hooks/common/update


### CGIT ###

echo ACTION: config file
cp files/cgitrc /etc/cgitrc

echo ACTION: httpd config
cp files/redirect.conf /etc/httpd/conf.d/dist-git/

# cgit/make_pkgs_list
echo ACTION: make pkgs list script
touch $DISTGITHOME/pkgs-git-repos-list
chown apache:apache $DISTGITHOME/pkgs-git-repos-list
chmod 0644 $DISTGITHOME/pkgs-git-repos-list
cp files/scripts/cgit_pkg_list.sh /usr/share/dist-git/
chmod 0755 /usr/share/dist-git/cgit_pkg_list.sh
# tbd: cron job

# cgit/clean_lock_cron
cp files/clean-lock.cron /etc/cron.d/cgit-clean-lock.cron
chmod 0644 /etc/cron.d/cgit-clean-lock.cron

# git/server
rm -f /usr/lib/systemd/system/git@.service
cp files/git@.service /usr/lib/systemd/system/git@.service
chmod 0644 /usr/lib/systemd/system/git@.service


### LOOKASIDE ###

echo ACTION: lookaside cache
mkdir -p /var/lib/dist-git/cache/lookaside/pkgs
chown apache:apache /var/lib/dist-git/cache/lookaside/pkgs

cp files/lookaside.conf /etc/httpd/conf.d/dist-git/
cp files/lookaside-upload.conf /etc/httpd/conf.d/dist-git/

mkdir /var/lib/dist-git/web
cp files/scripts/dist-git-upload.cgi /var/lib/dist-git/web/upload.cgi
chmod 0755 /var/lib/dist-git/web/upload.cgi


### OTHERS ###
groupadd cvsadmin
groupadd fedora-arm
groupadd fedora-sparc
groupadd fedora-ia64
groupadd fedora-s390
groupadd fedora-ppc
groupadd provenpackager
groupadd eclipse-sig
groupadd gnome-sig
groupadd infra-sig
groupadd kde-sig
groupadd python-sig
groupadd robotics-sig

git config --global user.name "John Root Doe"
git config --global user.email thebigbigboss@example.com

systemctl restart httpd
systemctl start git.socket


# user frank
useradd frank
USER="frank"
RSA="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC68iXNohFGki3huodI6FJi4ivRqkt8Dx/XWel8qmMuqezCoWNQN9w1mNvKaIfPGZCjBtLcKawNgliYvrOpBydHIgqMwXkw4rv3NBPDHKw5XVS4YsSZVdgE5JaEcLR85ahU4r25bfBP/Av0os0TkUzO9ij/6wNXGWpLs1611B2zI4IB0xpp9CVY4aEU3zgbDCHEMSqJZ39M4mJD2iitXpMF/yhvf4Z7jRWa2539HUXVvPp72rCQCgyvhJdcagQBHPWGT8gwipIL+RapF2Hyz+t8/zbQh1L+fwIL2w1tzSjq5SkdPlrNJjdW4XD56aUItRgjZJzwX12wLJY+CFwYqfTP frank@localhost.localdomain"

mkdir /home/$USER/.ssh
echo "command=\"HOME=/var/lib/dist-git/git/ /usr/share/gitolite3/gitolite-shell $USER\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty $RSA" > /home/$USER/.ssh/authorized_keys
chown -R $USER:$USER /home/$USER/.ssh
usermod -aG packager $USER

# packages
/usr/share/dist-git/dist_git_sync.sh
/usr/share/dist-git/cgit_pkg_list.sh


















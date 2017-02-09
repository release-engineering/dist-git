#!/bin/bash

export SCRIPTPATH="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export LANG=en_US.utf8

# primarily install git for the setup below
dnf -y install git

if [[ `pwd` =~ ^/mnt/tests.*$ ]]; then
    echo "Setting up native beaker environment."
    git clone https://pagure.io/dist-git.git
    export DISTGITROOTDIR=$SCRIPTPATH/dist-git
else
    echo "Setting up from source tree."
    export DISTGITROOTDIR=$SCRIPTPATH/../
fi

# install files from 'files'
cp -rT $SCRIPTPATH/files /

# install stuff needed for the test
dnf -y install vagrant
dnf -y install vagrant-libvirt
dnf -y install jq

# enable libvirtd for Vagrant (distgit)
systemctl enable libvirtd && systemctl start libvirtd
systemctl start virtlogd.socket # this is currently needed in f25 for vagrant to work with libvirtd

cd $DISTGITROOTDIR
vagrant up distgit

echo 'pkgs.fedoraproject.org 192.168.0.17' >> /etc/hosts

cd $SCRIPTPATH

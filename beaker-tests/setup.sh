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
dnf -y install git
dnf -y install wget
dnf -y install fedpkg
dnf -y install rpkg

# enable libvirtd for Vagrant (distgit)
systemctl enable libvirtd && systemctl start libvirtd
systemctl start virtlogd.socket # this is currently needed in f25 for vagrant to work with libvirtd

cd $DISTGITROOTDIR

DISTGITSTATUS=`mktemp`
vagrant status distgit | tee $DISTGITSTATUS
if grep -q 'not created' $DISTGITSTATUS; then
    vagrant up distgit
else
    vagrant reload distgit
fi
rm $DISTGITSTATUS

IPADDR=`vagrant ssh -c "ifconfig eth0 | grep -E 'inet\s' | sed 's/\s*inet\s*\([0-9.]*\).*/\1/'"`
echo "$IPADDR pkgs.example.org" >> /etc/hosts

if ! [ -f ~/.ssh/id_rsa ]; then
    mkdir -p ~/.ssh && chmod 700 ~/.ssh
    ssh-keygen -f ~/.ssh/id_rsa -N '' -q
fi

PUBKEY=`cat ~/.ssh/id_rsa.pub`
vagrant ssh -c "echo $PUBKEY > /tmp/id_rsa.pub.remote"

vagrant ssh -c '
sudo mkdir -p /home/clime/.ssh
sudo cp /tmp/id_rsa.pub.remote /home/clime/.ssh/authorized_keys
sudo chown -R clime:clime /home/clime/.ssh
sudo chmod 700 /home/clime/.ssh
sudo chmod 600 /home/clime/.ssh/authorized_keys
' distgit

vagrant ssh -c '
sudo mkdir -p /root/.ssh
sudo cp /tmp/id_rsa.pub.remote /root/.ssh/authorized_keys
sudo chmod 700 /root/.ssh
sudo chmod 600 /root/.ssh/authorized_keys
' distgit

cd $SCRIPTPATH

# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  ###  DistGit Fedora ###################################################
  config.vm.define "dist-git" do |distgit|
    distgit.vm.box = "fedora/32-cloud-base"

    distgit.vm.synced_folder ".", "/vagrant", type: "rsync"

    distgit.vm.provision "shell",
      inline: "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf"

    # Copy config files
    distgit.vm.provision "shell",
      inline: "rm -rf /tmp/pkgs-files",
      run: "always"

    distgit.vm.provision "file",
      source: "./beaker-tests/pkgs-files", destination: "/tmp/",
      run: "always"

    # update the system & install the packages
    distgit.vm.provision "shell",
      inline: "dnf clean all && dnf -y update || true" # || true cause dnf might return non-zero status (probly delta rpm rebuilt failed)

    distgit.vm.provision "shell",
      inline: "dnf install -y tito wget"

    distgit.vm.provision "shell",
      inline: "dnf builddep -y /vagrant/dist-git.spec",
      run: "always"

    distgit.vm.provision "shell",
      inline: "rm -rf /tmp/tito/noarch",
      run: "always"

    distgit.vm.provision "shell",
      inline: "cd /vagrant/ && tito build --test --rpm",
      run: "always"

    distgit.vm.provision "shell",
      inline: "dnf install -y /tmp/tito/noarch/*.rpm",
      run: "always"

    # setup config files
    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/ssl.conf /etc/httpd/conf.d/ssl.conf && restorecon -R /etc/httpd/conf.d/ssl.conf",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/lookaside-upload.conf /etc/httpd/conf.d/dist-git/ && restorecon -R /etc/httpd/conf.d/dist-git/",
      run: "always"

    # setup test user
    distgit.vm.provision "shell",
      inline: "useradd clime -G packager"

    distgit.vm.provision "shell",
      inline: "echo 'clime ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers"

    # start services
    distgit.vm.provision "shell",
      inline: "systemctl enable dist-git.socket && systemctl restart dist-git.socket",
      run: "always"

    distgit.vm.provision "shell",
      inline: "systemctl enable httpd && systemctl restart httpd",
      run: "always"

  end

  ###  DistGit CentOS 7 ###################################################
  config.vm.define "dist-git-centos-7" do |distgit|
    distgit.vm.box = "centos/7"

    distgit.vm.synced_folder ".", "/vagrant", type: "rsync"

    distgit.vm.provision "shell",
      inline: "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf"

    # Copy config files
    distgit.vm.provision "shell",
      inline: "rm -rf /tmp/pkgs-files",
      run: "always"

    distgit.vm.provision "file",
      source: "./beaker-tests/pkgs-files", destination: "/tmp/",
      run: "always"

    # enable epel7 repo
    distgit.vm.provision "shell",
      inline: "yum install -y epel-release",
      run: "always"

    # update the system & install the packages
    distgit.vm.provision "shell",
      inline: "yum clean all && yum -y update || true"

    distgit.vm.provision "shell",
      inline: "yum install -y tito wget net-tools"

    distgit.vm.provision "shell",
      inline: "yum-builddep -y /vagrant/dist-git.spec",
      run: "always"

    distgit.vm.provision "shell",
      inline: "rm -rf /tmp/tito/noarch",
      run: "always"

    distgit.vm.provision "shell",
      inline: "cd /vagrant/ && tito build --test --rpm",
      run: "always"

    distgit.vm.provision "shell",
      inline: "yum install -y /tmp/tito/noarch/*.rpm || true",
      run: "always"

    distgit.vm.provision "shell",
      inline: "yum install -y python-grokmirror",
      run: "always"

    # setup config files
    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/ssl.conf /etc/httpd/conf.d/ssl.conf && restorecon -R /etc/httpd/conf.d/ssl.conf",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/lookaside-upload.conf /etc/httpd/conf.d/dist-git/ && restorecon -R /etc/httpd/conf.d/dist-git/",
      run: "always"

    # setup test user
    distgit.vm.provision "shell",
      inline: "useradd clime -G packager"

    distgit.vm.provision "shell",
      inline: "echo 'clime ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers"

    # start services
    distgit.vm.provision "shell",
      inline: "systemctl enable dist-git.socket && systemctl restart dist-git.socket",
      run: "always"

    distgit.vm.provision "shell",
      inline: "systemctl enable httpd && systemctl restart httpd",
      run: "always"
  end

  ###  DistGit CentOS 8 ###################################################
  config.vm.define "dist-git-centos-8" do |distgit|
    distgit.vm.box = "centos/8"

    distgit.vm.synced_folder ".", "/vagrant", type: "rsync"

    distgit.vm.provision "shell",
      inline: "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf"

    # Copy config files
    distgit.vm.provision "shell",
      inline: "rm -rf /tmp/pkgs-files",
      run: "always"

    distgit.vm.provision "file",
      source: "./beaker-tests/pkgs-files", destination: "/tmp/",
      run: "always"

    # enable epel8 repo
    distgit.vm.provision "shell",
      inline: "yum install -y epel-release",
      run: "always"

    # update the system & install the packages
    distgit.vm.provision "shell",
      inline: "yum clean all && yum -y update || true"

    distgit.vm.provision "shell",
      inline: "yum install -y wget net-tools"

    distgit.vm.provision "shell",
      inline: "yum-builddep -y /vagrant/dist-git.spec",
      run: "always"

    distgit.vm.provision "shell",
      inline: "curl https://copr.fedorainfracloud.org/coprs/clime/rpkg-util/repo/epel-8/clime-rpkg-util-epel-8.repo > /etc/yum.repos.d/clime-rpkg-util-epel-8.repo",
      run: "always"

    distgit.vm.provision "shell",
      inline: "yum install -y rpkg",
      run: "always"

    distgit.vm.provision "shell",
      inline: "rm -rf /tmp/rpkg",
      run: "always"

    distgit.vm.provision "shell",
      inline: "cd /vagrant/ && rpkg local",
      run: "always"

    distgit.vm.provision "shell",
      inline: "yum install -y /tmp/rpkg/dist-git-*/noarch/*.rpm || true",
      run: "always"

    distgit.vm.provision "shell",
      inline: "yum install -y python-grokmirror",
      run: "always"

    # setup config files
    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/ssl.conf /etc/httpd/conf.d/ssl.conf && restorecon -R /etc/httpd/conf.d/ssl.conf",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/lookaside-upload.conf /etc/httpd/conf.d/dist-git/ && restorecon -R /etc/httpd/conf.d/dist-git/",
      run: "always"

    # setup test user
    distgit.vm.provision "shell",
      inline: "useradd clime -G packager"

    distgit.vm.provision "shell",
      inline: "echo 'clime ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers"

    # start services
    distgit.vm.provision "shell",
      inline: "systemctl enable dist-git.socket && systemctl restart dist-git.socket",
      run: "always"

    distgit.vm.provision "shell",
      inline: "systemctl enable httpd && systemctl restart httpd",
      run: "always"
  end
end

# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  ###  distgit  ###################################################
  config.vm.define "distgit" do |distgit|
    distgit.vm.box = "fedora/27-cloud-base"

    distgit.vm.synced_folder ".", "/vagrant", type: "rsync"

    distgit.vm.provision "shell",
      inline: "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf"

    # Update the system
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

    # setup test user
    distgit.vm.provision "shell",
      inline: "useradd clime -G packager"

    distgit.vm.provision "shell",
      inline: "echo 'clime ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers"

    distgit.vm.provision "shell",
      inline: "rm -rf /tmp/pkgs-files",
      run: "always"

    distgit.vm.provision "file",
      source: "./beaker-tests/pkgs-files", destination: "/tmp/pkgs-files",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/pkgs.example.org.pem /etc/pki/tls/certs/pkgs.example.org.pem && restorecon -R /etc/pki/tls/certs/",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/ca-bundle.crt /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem && restorecon -R /etc/pki/ca-trust/extracted/pem/",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs-files/lookaside-upload.conf /etc/httpd/conf.d/dist-git/ && restorecon -R /etc/httpd/conf.d/dist-git/",
      run: "always"

    distgit.vm.provision "shell",
      inline: "systemctl enable dist-git.socket && systemctl restart dist-git.socket",
      run: "always"

    distgit.vm.provision "shell",
      inline: "systemctl enable httpd && systemctl restart httpd",
      run: "always"

    distgit.vm.provision "shell",
      inline: "dnf install -y python-grokmirror",
      run: "always"

  end
end

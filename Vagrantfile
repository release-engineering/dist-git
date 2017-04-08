# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  ###  distgit  ###################################################
  config.vm.define "distgit" do |distgit|
    distgit.vm.box = "fedora/25-cloud-base"

    distgit.vm.synced_folder ".", "/vagrant", type: "rsync"

    distgit.vm.provision "shell",
      inline: "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf",
      run: "always"

    # Update the system
    distgit.vm.provision "shell",
      inline: "dnf clean all && sudo dnf -y update || true" # || true cause dnf might return non-zero status (probly delta rpm rebuilt failed)

    distgit.vm.provision "shell",
      inline: "dnf install -y tito wget"

    distgit.vm.provision "shell",
      inline: "dnf builddep -y /vagrant/dist-git.spec",
      run: "always"

    distgit.vm.provision "shell",
      inline: "cd /vagrant/ && tito build -i --test --rpm",
      run: "always"

    distgit.vm.provision "shell",
      inline: "cp /etc/httpd/conf.d/dist-git/lookaside-upload.conf.example /etc/httpd/conf.d/dist-git/lookaside-upload.conf",
      run: "always"

    distgit.vm.provision "file",
      source: "./beaker-tests/pkgs-files/pkgs.example.org.pem", destination: "/tmp/pkgs.example.org.pem",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/pkgs.example.org.pem /etc/pki/tls/certs/pkgs.example.org.pem && restorecon -R /etc/pki/tls/certs/",
      run: "always"

    distgit.vm.provision "file",
      source: "./beaker-tests/pkgs-files/ca-bundle.crt", destination: "/tmp/ca-bundle.crt",
      run: "always"

    distgit.vm.provision "shell",
      inline: "mv /tmp/ca-bundle.crt /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem && restorecon -R /etc/pki/ca-trust/extracted/pem/",
      run: "always"

    distgit.vm.provision "shell",
      inline: "systemctl enable dist-git.socket && systemctl restart dist-git.socket",
      run: "always"

    distgit.vm.provision "shell",
      inline: "systemctl enable httpd && systemctl restart httpd",
      run: "always"

    distgit.vm.provision "shell",
      inline: "useradd clime -G packager"

    distgit.vm.provision "shell",
      inline: "echo 'clime   ALL=(ALL)       NOPASSWD: ALL' >> /etc/sudoers"

  end
end

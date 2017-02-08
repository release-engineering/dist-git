# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

  ###  distgit  ###################################################
  config.vm.define "distgit" do |distgit|
    distgit.vm.box = "fedora/25-cloud-base"

    distgit.vm.network "forwarded_port", guest: 80, host: 5000

    distgit.vm.synced_folder ".", "/vagrant", type: "rsync"

    distgit.vm.network "private_network", ip: "192.168.242.53"

    # Update the system
    distgit.vm.provision "shell",
      inline: "sudo dnf clean all && sudo dnf -y update || true" # || true cause dnf might return non-zero status (probly delta rpm rebuilt failed)

    distgit.vm.provision "shell",
      inline: "sudo dnf builddep -y /vagrant/dist-git.spec --allowerasing" # FIXME: remove --allowerasing, which was added due to this command failing on python-requests installation if python2-requests is already installed

    distgit.vm.provision "shell",
      inline: "sudo dnf install -y tito wget",
      run: "always"

    distgit.vm.provision "shell",
      inline: "sudo dnf builddep -y /vagrant/dist-git.spec",
      run: "always"

    distgit.vm.provision "shell",
      inline: "cd /vagrant/ && tito build -i --test --rpm",
      run: "always"

    distgit.vm.provision "shell",
      inline: "sudo systemctl enable dist-git.socket && sudo systemctl start dist-git.socket",
      run: "always"

    distgit.vm.provision "shell",
      inline: "sudo systemctl enable httpd && sudo systemctl start httpd",
      run: "always"

  end
end

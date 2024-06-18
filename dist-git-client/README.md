Get sources from DistGit
========================

A simple, configurable python utility that is able to clone package sources from
a DistGit repository, download sources from the corresponding lookaside cache
location, and generate source RPM.

The utility is able to automatically map the .git/config clone URL into the
corresponding DistGit instance configuration.


Usage
-----

Building package from DistGit is as simple as:

    $ dist-git-client clone tar
    INFO: Checked call: git clone https://src.fedoraproject.org/rpms/tar.git
    Cloning into 'tar'...
    ...
    Resolving deltas: 100% (802/802), done.

    $ cd tar

    $ dist-git-client sources
    INFO: Reading stdout from command: git rev-parse --abbrev-ref HEAD
    INFO: Reading sources specification file: sources
    INFO: Downloading tar-1.35.tar.xz
    INFO: Reading stdout from command: curl --help all
    INFO: Calling: curl -H Pragma: -o tar-1.35.tar.xz --location --connect-timeout 60 --retry 3 --retry-delay 10 --remote-time --show-error --fail --retry-all-errors https://src.fedoraproject.org/repo/pkgs/rpms/tar/tar-1.35.tar.xz/sha512/8b84ed661e6c878fa33eb5c1808d20351e6f40551ac63f96014fb0d0b9c72d5d94d8865d39e36bcb184fd250f84778a3b271bbd8bd2ceb69eece0c3568577510/tar-1.35.tar.xz
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100 2262k  100 2262k    0     0  1983k      0  0:00:01  0:00:01 --:--:-- 1984k
    INFO: Reading stdout from command: sha512sum tar-1.35.tar.xz
    INFO: Downloading tar-1.35.tar.xz.sig
    INFO: Calling: curl -H Pragma: -o tar-1.35.tar.xz.sig --location --connect-timeout 60 --retry 3 --retry-delay 10 --remote-time --show-error --fail --retry-all-errors https://src.fedoraproject.org/repo/pkgs/rpms/tar/tar-1.35.tar.xz.sig/sha512/00e5c95bf8015f75f59556a82ed7f50bddefe89754c7ff3c19411aee2f37626a5d65c33e18b87f7f8f96388d3f175fd095917419a3ad1c0fc9d6188088bac944/tar-1.35.tar.xz.sig
      % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                     Dload  Upload   Total   Spent    Left  Speed
    100    95  100    95    0     0    270      0 --:--:-- --:--:-- --:--:--   270
    INFO: Reading stdout from command: sha512sum tar-1.35.tar.xz.sig

    $ dist-git-client srpm
    ...
    Wrote: /tmp/tar-1.35-3.src.rpm

    $ mock /tmp/tar-1.35-3.src.rpm
    ...
    Wrote: /builddir/build/RPMS/tar-debuginfo-1.35-3.fc39.x86_64.rpm
    Wrote: /builddir/build/RPMS/tar-1.35-3.fc39.x86_64.rpm
    Wrote: /builddir/build/RPMS/tar-debugsource-1.35-3.fc39.x86_64.rpm
    ...
    Finish: run


Configuration
-------------

The project provides also a predefined set of existing (public) DistGit
instances (Fedora, CentOS, Fedora Copr).  Check the configuration file
`/etc/dist-git-client/default.ini` out for the configuration documentation,
and feel free to drop another INI configuration file into the
`/etc/dist-git-client/` directory.


Install
-------

From regular Fedora/EPEL repositories:

    $ dnf install -y dist-git-client

From source code:

    $ tito build --rpm --install

Without installation - directly from Git (development/debugging use-case, no support):

    $ ./dist-git-client ....

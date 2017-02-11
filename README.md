DistGit
=======

DistGit (Distributed Git) is Git with additional data storage. It is designed to hold content of source rpms and consists of these three main components:

 1. Git repositories
 2. Lookaside cache to store source tarballs
 3. Scripts to manage both

How Does It Work
----------------

RPM source package typically contains a spec file and the sources (upstream tarball + additional patches). Source tarballs, being binary and potentially large, are not very well suited to be placed in a Git repository. On each their update, Git would produce a huge, meaningless diff. That's why DistGit was introduced as it employs an efficient lookaside cache where the tarballs can be stored. The Git repo itself can then be left to do what it does best: keep track of changes on the spec file, downstream patches, and an additional text file called `sources` that contains link to the source tarball in the lookaside cache.

![storage](/images/storage.png)

User Guide
----------

The project is prepared to be built as an RPM package. You can easily build it on [Fedora](https://getfedora.org/) or [CentOS](https://www.centos.org/) using a tool called [Tito](https://github.com/dgoodwin/tito).

#### 1. Build and Install the Package:

To build the current release, use the following command in the repo directory:
`$ tito build --rpm`

Install the resulting RPM package:
`# dnf install /path/to/the-package.rpm`

#### 2. Configuration:

Enable the lookaside cache by using and modifying the example httpd config:

```
# cd /etc/httpd/conf.d/dist-git/
# cp lookaside-upload.conf.example lookaside-upload.conf
# vim lookaside-upload.conf
```

Lookaside Cache uses https communication and client authenticates with ssl client certificate. The Dist Git service provider needs to issue the client certificate for every user.

#### 3. Users and Groups:

All DistGit users need to:
 1. have an ssh server access with private key authentication
 2. be in a *packager* group on the server
 3. be provided with an ssl client certificate to authenticate with the lookaside cache

#### 4. Install DistGit Web Interface:

Install Cgit, the web interface for Git:
`# dnf install cgit`

And point it to the DistGit repositories:
```
# echo "project-list=/srv/git/pkgs-git-repos-list" >> /etc/cgitrc
# echo "scan-path=/srv/git/repositories/" >> /etc/cgitrc
```

It is useful to comment out `cache-size` entry in /etc/cgitrc (or set it to zero) to always get up-to-date repository state at each page refresh.

The web interface will be available on address like `http://your-server/cgit`.

#### 5. Systemd Services:

```
# systemctl start sshd
# systemctl start httpd
# systemctl start dist-git.socket
```

#### 6. DistGit client tools:

To interact with DistGit server, you can use use rpkg command-line tool or python pyrpkg library.

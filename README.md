DistGit
=======

DistGit (Distribution Git) is Git with additional data storage. It is designed to hold content of source rpms and consists of these three main components:

 1. Git repositories
 2. Lookaside cache to store source tarballs
 3. Scripts to manage both

Read here for information about the most recent release: https://github.com/release-engineering/dist-git/wiki

How Does It Work
----------------

RPM source package typically contains a spec file and the sources (upstream tarball + additional patches). Source tarballs, being binary and potentially large, are not very well suited to be placed in a Git repository. On each their update, Git would produce a huge, meaningless diff. That's why DistGit was introduced as it employs an efficient lookaside cache where the tarballs can be stored. The Git repo itself can then be left to do what it does best: keep track of changes on the spec file, downstream patches, and an additional text file called `sources` that contains link to the source tarball in the lookaside cache.

![storage](/images/storage.png)

Video Tutorial
--------------

[![DistGit video tutorial](images/tutorial.png)](https://www.youtube.com/watch?v=VsnJymZRQOM "DistGit video tutorial")

User Guide
----------

#### 1. Build and Install the Package:

The project is prepared to be built as an RPM package. You can easily build it on [Fedora](https://getfedora.org/) or [CentOS](https://www.centos.org/) with EPEL7 enabled using a tool called [tito](https://github.com/rpm-software-management/tito).
To build the current release, use the following command in the repo directory:

```
$ tito build --rpm 
```

Install the resulting RPM package:

```
# tito build --rpm -i
```

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

```
# dnf install cgit
```

And point it to the DistGit repositories:

```
echo "scan-path=/var/lib/dist-git/git/" >> /etc/cgitrc
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

To interact with DistGit server, you can use use [rpkg](https://pagure.io/rpkg-util) or [fedpkg](https://pagure.io/fedpkg) command-line tools.

#### 7. Deployment

You can see examples of Ansible deployment scripts in
[Fedora Infastructure dist-git role] and [Copr dist-git role].


### Related

* [Source-git](https://packit.dev/docs/source-git/) - project started in 2020. Intended as layer on top of dist-git.

Developer Guide
---------------

#### Unit tests

```
nosetests -vs .
```

#### Integration tests

Please, see `beaker-tests/README.md`.

LICENSE
-------

Whole project use MIT license. File upload.cgi uses GPLv1.


[Fedora Infastructure dist-git role]: https://pagure.io/fedora-infra/ansible/blob/main/f/roles/distgit
[Copr dist-git role]: https://pagure.io/fedora-infra/ansible/blob/main/f/roles/copr/dist_git

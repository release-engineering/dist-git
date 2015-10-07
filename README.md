**This project is under developement. Please do not use it in production. Ideas, issues and patches are very welcome.**

Dist Git
========

Dist Git is a remote Git repository specifically designed to hold RPM package sources. It consists of three main modules:

 1. Git repository with permissions managed by [Gitolite](http://gitolite.com/gitolite/index.html)
 2. Lookaside cache to store source tarballs
 3. Scripts to manage

How Does It Work
----------------

### Hosting Files

An RPM package repository typically consists of a spec file and the sources itself. Sources are most often taken from the upstream as they are and packed as a tarball. The sources can contain large files like virtual machine images, which, in some cases, can grow up to several GB. Those binary files can not be stored in git effectively - so the Dist Git stores them in a separate place called Lookaside Cache and only a text link to the cache is stored in the git itself.

![storage](/images/storage.png)

### Communication

The Dist Git server repeatedly asks a package database for information about packages. This information contains a list of packages and other information. Each package can have a list of users or groups entitled to commit to this package and a list of platforms for which the package is built. Sources for each platform are held in corresponding branches.

Users can interact with the Dist Git server using a client probably based on [rpkg](https://fedorahosted.org/rpkg/). The client authenticates with an ssh certificate for git communication and with an http client certificate for uploads to the lookaside cache.

![server-communication](/images/server-communication.png)

#### Package Database Communication
The following is an example JSON data coming from the Package Database which would create two packages: *copr-frontend* and *copr-backend*. The first package would be for Fedora 21 only and permissions to commit into this repo would be granted to users *mirek*, *adam* and anyone in the group *provenpackager*. The *copr-backend* package would be for Fedora 21 and CentOS 7. The permissions would be processed the same way as for the first package.

```JSON
"packageAcls": {
    "copr-frontend": {
        "fedora-21": {
            "commit": {
                "groups": ["provenpackager"],
                "people": ["mirek", "adam"]
            }
        }
    },
    "copr-backend": {
        "fedora-21": {
            "commit": {
                "groups": ["provenpackager"],
                "people": ["mirek", "valentin"]
            }
        },
        "centos-7": {
            "commit": {
                "groups": ["provenpackager"],
                "people": ["mirek", "valentin"]
            }
        }
    }
}
```

The final result would consist of two package repositories:
- *copr-frontend* with a single branch: *fedora-21*
- *copr-backend* with two branches: *fedora-21* and *centos-7*

#### Client Authentication and Authorization

In order to make changes in the package repositories, client needs to have a permission to do that. Both Git and Lookaside Cache have their own auth process.

Git uses ssh communication and client authenticates with public key. Each user needs to have an account on the server and be in a *packager* group. Their ssh shell must be set to "`HOME=/var/lib/dist-git/git /usr/share/gitolite3/gitolite-shell $USERNAME`" in order to have authorization working.

Authorization is done by Gitolite. The configuration file describing all the permisions is automatically generated each time a Package Database is queried. Gitolite uses system users and groups.

Lookaside Cache uses https communication and client authenticates with ssl client certificate. The Dist Git service provider needs to issue the client certificate for every user.

There is no authentication needed in order to read from the server.


Installation Guide 
-----------------

The project is prepared to be built as an RPM package. You can easily build it on [Fedora](https://getfedora.org/) or [CentOS](https://www.centos.org/) using a tool called [Tito](https://github.com/dgoodwin/tito).

#### 1. Build and Install the Package:

To build the current release, use the following command in the repo directory:  
`$ tito build --rpm`  

Install the resulting RPM package:  
`# yum install /path/to/the-package.rpm`  

#### 2. Configuration:

Edit the configuration file at `/etc/dist-git/dist-git.conf` to match your requirements. The file contains several examples and tips that should help you with your setup.

Enable the lookaside cache by using and modifying the example httpd scripts:
```
# cd /etc/httpd/conf.d/
# cp ssl.conf.example ssl.conf

# cd /etc/httpd/conf.d/dist-git/
# cp lookaside-upload.conf.example lookaside-upload.conf
# vim lookaside-upload.conf
```

#### 3. Users and Groups:

All users need to:
 1. have an ssh access with private key authentication
 2. be in a *packager* group
 3. have their ssh shell restricted to "`HOME=/var/lib/dist-git/git /usr/share/gitolite3/gitolite-shell $USERNAME`"
 4. be provided with an ssl client certificate to authenticate with the lookaside cache

An example setup of the first three steps could look like this:
```
USER="frank"
RSA="ssh-rsa AAA...YqfTP frank@example.com"

useradd $USER
usermod -aG packager $USER
mkdir /home/$USER/.ssh
echo "command=\"HOME=/var/lib/dist-git/git/ /usr/share/gitolite3/gitolite-shell $USER\" $RSA" > /home/$USER/.ssh/authorized_keys
```

#### 4. Install the Web Interface:

Install Cgit, the web interface for git:
`# yum install cgit`  

And point it to the distgit repositories:  
```
# echo "project-list=/var/lib/dist-git/git/pkgs-git-repos-list" >> /etc/cgitrc
# echo "scan-path=/var/lib/dist-git/git/rpms/" >> /etc/cgitrc
```

The web interface will be available on address like `http://your-server/cgit`.

#### 5. Systemd Services:

```
# systemctl start sshd
# systemctl start httpd
# systemctl start dist-git.socket
```

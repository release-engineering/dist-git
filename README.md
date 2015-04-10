Dist Git
========

Dist Git is a remote Git repository specificaly designed to hold RPM package sources. It consists of three main modules:

 1. Git repository with permissions managed by [Gitolite](http://gitolite.com/gitolite/index.html)
 2. Lookaside cache to store source tarballs
 3. Scripts to manage

How does it work
----------------

The Dist Git server repeatedly asks a package database for information about packages. This information contains a list of packages and other information. Each package can have a list of users or groups entitled to commit to this package and a list of platforms for which the package is built. Sources for each platform are held in corresponding branches.

User cat interact with the Dist Git server using client probably based on [rpkg](https://fedorahosted.org/rpkg/). The client authenticates with an ssh certificate for git communication and with an http client certificate for uploads to the lookaside cache.

![server-communication](/images/server-communication.png)

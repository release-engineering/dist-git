Name:           dist-git
Version:        0.8
Release:        1%{?dist}
Summary:        Package source version control system

Group:          Applications/Productivity

# upload.cgi uses GPLv1 and pkgdb_sync_git_branches.py uses GPLv2+
License:        MIT and GPLv1 and GPLv2+
URL:            https://github.com/release-engineering/dist-git
# Source is created by
# git clone https://github.com/release-engineering/dist-git.git
# cd dist-git
# tito build --tgz
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  systemd

Requires:       httpd
Requires:       gitolite3
Requires:       perl-Sys-Syslog
Requires:       git-daemon
Requires:       python-requests
Requires:       /usr/sbin/semanage
Requires:       mod_ssl
Requires:       fedmsg
Requires:       cronie
Requires(pre):  shadow-utils

%description
Dist Git is a remote Git repository specifically designed to hold RPM
package sources.


%prep
%setup -q


%build



%pre
getent group packager > /dev/null || \
    groupadd -r packager

getent group gen-acls > /dev/null || \
    groupadd -r gen-acls

getent passwd gen-acls > /dev/null || \
    useradd -r -g gen-acls -G packager -s /bin/bash \
            -d %{_sharedstatedir}/dist-git/git gen-acls



%install

# ------------------------------------------------------------------------------
# /usr/share/ .... static files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{_datadir}/dist-git

cp -a scripts/dist-git/* %{buildroot}%{_datadir}/dist-git/


# ------------------------------------------------------------------------------
# /etc/ .......... config files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{_sysconfdir}/dist-git
install -d %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git
install -d %{buildroot}%{_sysconfdir}/cron.d/dist-git
mkdir -p   %{buildroot}%{_unitdir}

cp -a configs/dist-git/dist-git.conf  %{buildroot}%{_sysconfdir}/dist-git/
cp -a configs/gitolite/gitolite.rc    %{buildroot}%{_sysconfdir}/dist-git/
cp -a configs/httpd/dist-git.conf     %{buildroot}%{_sysconfdir}/httpd/conf.d/
cp -a configs/httpd/ssl.conf.example  %{buildroot}%{_sysconfdir}/httpd/conf.d/
cp -a configs/httpd/dist-git/* %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git/
cp -a configs/cron/*           %{buildroot}%{_sysconfdir}/cron.d/dist-git/
cp -a configs/systemd/*        %{buildroot}%{_unitdir}/


# ------------------------------------------------------------------------------
# /var/lib/ ...... dynamic persistent files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{_sharedstatedir}/dist-git
install -d %{buildroot}%{_sharedstatedir}/dist-git/git
install -d %{buildroot}%{_sharedstatedir}/dist-git/git/rpms
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/conf
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/logs
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/local
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/local/VREF
install -d %{buildroot}%{_sharedstatedir}/dist-git/cache
install -d %{buildroot}%{_sharedstatedir}/dist-git/cache/lookaside
install -d %{buildroot}%{_sharedstatedir}/dist-git/cache/lookaside/pkgs
install -d %{buildroot}%{_sharedstatedir}/dist-git/web
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/hooks
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/hooks/common

cp -a scripts/httpd/upload.cgi %{buildroot}%{_sharedstatedir}/dist-git/web/

cp -a scripts/git/hooks/update-block-push-origin \
      %{buildroot}%{_sharedstatedir}/dist-git/gitolite/local/VREF/update-block-push-origin

ln -f -s %{_sysconfdir}/dist-git/gitolite.rc \
         %{buildroot}%{_sharedstatedir}/dist-git/git/.gitolite.rc

ln -f -s %{_sharedstatedir}/dist-git/gitolite \
         %{buildroot}%{_sharedstatedir}/dist-git/git/.gitolite

ln -f -s %{_sharedstatedir}/dist-git/git/rpms \
         %{buildroot}%{_sharedstatedir}/dist-git/git/repositories




%files

%license LICENSE
%doc README.md

# ------------------------------------------------------------------------------
# /usr/share/ .... static files
# ------------------------------------------------------------------------------
%dir              %{_datadir}/dist-git
%attr (755, -, -) %{_datadir}/dist-git/*


# ------------------------------------------------------------------------------
# /etc/ .......... config files
# ------------------------------------------------------------------------------
%dir                   %{_sysconfdir}/dist-git
%config(noreplace)     %{_sysconfdir}/dist-git/dist-git.conf
%config(noreplace)     %{_sysconfdir}/dist-git/gitolite.rc
%config(noreplace)     %{_sysconfdir}/httpd/conf.d/dist-git.conf
%config                %{_sysconfdir}/httpd/conf.d/ssl.conf.example
%dir                   %{_sysconfdir}/httpd/conf.d/dist-git
%config(noreplace)     %{_sysconfdir}/httpd/conf.d/dist-git/*
%dir                   %{_sysconfdir}/cron.d/dist-git
%config(noreplace)     %{_sysconfdir}/cron.d/dist-git/cgit_pkg_list.cron
%config(noreplace)     %{_sysconfdir}/cron.d/dist-git/dist_git_sync.cron
%{_unitdir}/dist-git@.service
%{_unitdir}/dist-git.socket


# ------------------------------------------------------------------------------
# /var/lib/ ...... dynamic persistent files
# ------------------------------------------------------------------------------

# non-standard-dir-perm:
# - git repositories and their contents must have w permission for their creators
%dir                              %{_sharedstatedir}/dist-git
%dir                              %{_sharedstatedir}/dist-git/git
%attr (2775, -, packager)         %{_sharedstatedir}/dist-git/git/rpms
%dir                              %{_sharedstatedir}/dist-git/gitolite
%attr (755, gen-acls, gen-acls)   %{_sharedstatedir}/dist-git/gitolite/conf
# non-standard-dir-perm:
# - write access needed into log directory for gitolite
%attr (775, gen-acls, packager)   %{_sharedstatedir}/dist-git/gitolite/logs
%dir                              %{_sharedstatedir}/dist-git/gitolite/local
# non-standard-dir-perm:
# - write access needed for gitolite admin groups
%attr (775, gen-acls, packager)   %{_sharedstatedir}/dist-git/gitolite/local/VREF
# non-standard-executable-perm:
# - write access needed for gitolite admin groups
# - exec permission needed for execution by git (it's a git hook script)
%attr (775, gen-acls, packager)   %{_sharedstatedir}/dist-git/gitolite/local/VREF/update-block-push-origin
# non-standard-dir-perm:
# - write access needed for gitolite admin groups
%attr (770, -, packager)          %{_sharedstatedir}/dist-git/gitolite/hooks
# script-without-shebang:
# zero-length:
# - initial empty file required by gitolite with the correct perms
%dir                              %{_sharedstatedir}/dist-git/gitolite/hooks/common
%dir                              %{_sharedstatedir}/dist-git/web
%attr (755, apache, apache)       %{_sharedstatedir}/dist-git/web/upload.cgi
%dir                              %{_sharedstatedir}/dist-git/cache
%dir                              %{_sharedstatedir}/dist-git/cache/lookaside
%attr (755, apache, apache)       %{_sharedstatedir}/dist-git/cache/lookaside/pkgs
%{_sharedstatedir}/dist-git/git/repositories
%{_sharedstatedir}/dist-git/git/.gitolite
%{_sharedstatedir}/dist-git/git/.gitolite.rc



%changelog
* Thu Apr 23 2015 Adam Samalik <asamalik@redhat.com> 0.8-1
- review update (asamalik@redhat.com)

* Wed Apr 22 2015 Adam Samalik <asamalik@redhat.com> 0.7-1
- git hooks permissions (asamalik@redhat.com)
- noreplace configs (asamalik@redhat.com)
- fixes after rpmlint (asamalik@redhat.com)

* Wed Apr 22 2015 Adam Samalik <asamalik@redhat.com> 0.6-1
- license + description (asamalik@redhat.com)
- cron files fix (asamalik@redhat.com)

* Wed Apr 15 2015 Adam Samalik <asamalik@redhat.com> 0.5-1
- git hook: update-block-push-origin (asamalik@redhat.com)
- lookaside-upload config comments (asamalik@redhat.com)
- gen-acls user fix (asamalik@redhat.com)
- ssl httpd configs as examples (asamalik@redhat.com)

* Fri Apr 10 2015 Adam Samalik <asamalik@redhat.com> 0.4-1
- spec and config fix
- systemd services
* Tue Mar 31 2015 Adam Samalik <asamalik@redhat.com> 0.3-1
- alpha package (asamalik@redhat.com)

* Mon Mar 30 2015 Adam Samalik <asamalik@redhat.com> 0.2-1
- new package built with tito



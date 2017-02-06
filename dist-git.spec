%global selinux_variants mls targeted
%global selinux_policyver %(%{__sed} -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp || echo 0.0.0)
%global modulename dist_git
%global installdir /srv

Name:           dist-git
Version:        0.13
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
Requires:       perl(Sys::Syslog)
Requires:       git-daemon
Requires:       python-requests
Requires:       mod_ssl
Requires:       fedmsg
Requires(pre):  shadow-utils

%description
Dist Git is a remote Git repository specifically designed to hold RPM
package sources.


%package selinux
Summary:        SELinux support for dist-git

BuildRequires:  checkpolicy
BuildRequires:  policycoreutils
BuildRequires:  selinux-policy-devel
BuildRequires:  hardlink

Requires:       %name = %version-%release
%if "%{_selinux_policy_version}" != ""
Requires:       selinux-policy >= %{selinux_policyver}
%endif
Requires(post):   /usr/sbin/semodule, /sbin/restorecon
Requires(postun): /usr/sbin/semodule, /sbin/restorecon


%description selinux
Dist Git is a remote Git repository specifically designed to hold RPM
package sources.

This package includes SELinux support.


%prep
%setup -q


%build
# ------------------------------------------------------------------------------
# SELinux
# ------------------------------------------------------------------------------
cd selinux
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv %{modulename}.pp %{modulename}.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -


%pre
# ------------------------------------------------------------------------------
# Users and Groups
# ------------------------------------------------------------------------------
getent group packager > /dev/null || \
    groupadd -r packager

getent group gen-acls > /dev/null || \
    groupadd -r gen-acls

getent passwd gen-acls > /dev/null || \
    useradd -r -g gen-acls -G packager -s /bin/bash \
            -d /srv/git gen-acls # gid: 417


%install
# ------------------------------------------------------------------------------
# /usr/local/bin ........... scripts
# ------------------------------------------------------------------------------
install -d %{buildroot}/usr/local/bin/
cp -a scripts/dist-git/* %{buildroot}/usr/local/bin/

# ------------------------------------------------------------------------------
# /etc/ .......... config files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{_sysconfdir}/dist-git
install -d %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git
mkdir -p   %{buildroot}%{_unitdir}

cp -a configs/dist-git/dist-git.conf  %{buildroot}%{_sysconfdir}/dist-git/
cp -a configs/httpd/dist-git.conf     %{buildroot}%{_sysconfdir}/httpd/conf.d/
cp -a configs/httpd/ssl.conf.example  %{buildroot}%{_sysconfdir}/httpd/conf.d/
cp -a configs/httpd/dist-git/* %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git/
cp -a configs/systemd/*        %{buildroot}%{_unitdir}/

# ------------------------------------------------------------------------------
# /var/lib/ ...... dynamic persistent files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{installdir}
install -d %{buildroot}%{installdir}/git
install -d %{buildroot}%{installdir}/git/repositories
install -d %{buildroot}%{installdir}/cache
install -d %{buildroot}%{installdir}/cache/lookaside
install -d %{buildroot}%{installdir}/cache/lookaside/pkgs
install -d %{buildroot}%{installdir}/web

cp -a scripts/httpd/upload.cgi %{buildroot}%{installdir}/web/

# ------------------------------------------------------------------------------
# SELinux
# ------------------------------------------------------------------------------
cd selinux
for selinuxvariant in %{selinux_variants}
do
  install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  install -p -m 644 %{modulename}.pp.${selinuxvariant} \
    %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp
done
cd -

/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux


%post selinux
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp &> /dev/null || :
done
%{_sbindir}/restorecon -Rv /srv/git/ || :
%{_sbindir}/restorecon -Rv /srv/cache/ || :
%{_sbindir}/restorecon -Rv /srv/web/ || :


%postun selinux
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}
  do
     /usr/sbin/semodule -s ${selinuxvariant} -r %{modulename} &> /dev/null || :
  done
fi


%files
# ------------------------------------------------------------------------------
# Docs
# ------------------------------------------------------------------------------
%license LICENSE
%doc README.md

# ------------------------------------------------------------------------------
# /etc/ .......... config files
# ------------------------------------------------------------------------------
%dir                   %{_sysconfdir}/dist-git
%config(noreplace)     %{_sysconfdir}/dist-git/dist-git.conf
%config(noreplace)     %{_sysconfdir}/httpd/conf.d/dist-git.conf
%config                %{_sysconfdir}/httpd/conf.d/ssl.conf.example
%dir                   %{_sysconfdir}/httpd/conf.d/dist-git
%config(noreplace)     %{_sysconfdir}/httpd/conf.d/dist-git/*

%{_unitdir}/dist-git@.service
%{_unitdir}/dist-git.socket

# ------------------------------------------------------------------------------
# /var/lib/ ...... dynamic persistent files
# ------------------------------------------------------------------------------

# non-standard-dir-perm:
# - git repositories and their contents must have w permission for their creators
%dir                              %{installdir}
%dir                              %{installdir}/git
%attr (2775, -, packager)         %{installdir}/git/repositories
%dir                              %{installdir}/web
%attr (755, apache, apache)       %{installdir}/web/upload.cgi
%dir                              %{installdir}/cache
%dir                              %{installdir}/cache/lookaside
%attr (775, apache, apache)       %{installdir}/cache/lookaside/pkgs
%attr (755, root, root) /usr/local/bin/mkbranch
%attr (755, root, root) /usr/local/bin/mkbranch_branching
%attr (755, root, root) /usr/local/bin/cgit_pkg_list
%attr (755, root, root) /usr/local/bin/setup_git_package

%files selinux
%defattr(-,root,root,0755)
%doc selinux/*
%{_datadir}/selinux/*/%{modulename}.pp


%changelog
* Wed Aug 05 2015 Adam Samalik <asamalik@redhat.com> 0.13-1
- optional cgit_pkg_list.sh parameter (asamalik@redhat.com)
- change mv to cp + rm (asamalik@redhat.com)
- update config to not be Fedora specific (asamalik@redhat.com)
- Change: lookaside dir perms + cgit_pkg_list.sh (asamalik@redhat.com)
* Mon Jul 20 2015 Adam Samalik <asamalik@redhat.com> 0.12-1
- config update (asamalik@redhat.com)
- Upload files to new and old paths + remove email (asamalik@redhat.com)

* Tue May 05 2015 Adam Samalik <asamalik@redhat.com> 0.11-1
- SELinux subpackage
* Mon Apr 27 2015 Adam Samalik <asamalik@redhat.com> 0.10-1
- perl require and files update (asamalik@redhat.com)

* Thu Apr 23 2015 Adam Samalik <asamalik@redhat.com> 0.9-1
- update hook update (asamalik@redhat.com)

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



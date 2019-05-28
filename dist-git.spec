%global selinux_variants mls targeted
%global modulename dist_git
%global installdir /var/lib/dist-git

Name:           dist-git
Version:        1.12
Release:        1%{?dist}
Summary:        Package source version control system

# upload.cgi uses GPLv1
License:        MIT and GPLv1
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
Requires:       dist-git-selinux
Requires:       git
Requires:       git-daemon
Requires:       mod_ssl
Requires:       crudini
Requires:       moreutils
Requires(pre):  shadow-utils

%if 0%{?rhel} && 0%{?rhel} < 8
Requires:       python-requests
Requires:       python-configparser
Requires:       python-grokmirror
Requires:       fedmsg
%else
Requires:       python3-requests
Recommends:     python3-grokmirror
Requires:       python3-fedmsg
%endif

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
Requires:       selinux-policy >= %{_selinux_policy_version}
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
exit 0


%install
# ------------------------------------------------------------------------------
# /usr/share/ ........... scripts
# ------------------------------------------------------------------------------
install -d %{buildroot}%{_datadir}/dist-git/
cp -a scripts/dist-git/* %{buildroot}%{_datadir}/dist-git/

# ------------------------------------------------------------------------------
# /etc/ .......... config files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{_sysconfdir}/dist-git
cp -a configs/dist-git/dist-git.conf %{buildroot}%{_sysconfdir}/dist-git/
install -d %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git
mkdir -p   %{buildroot}%{_unitdir}

cp -a configs/httpd/dist-git.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/
cp -a configs/httpd/dist-git/* %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git/
cp -a configs/systemd/*        %{buildroot}%{_unitdir}/

# ------------------------------------------------------------------------------
# /var/lib/ ...... dynamic persistent files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{installdir}
install -d %{buildroot}%{installdir}/git
install -d %{buildroot}%{installdir}/cache
install -d %{buildroot}%{installdir}/cache/lookaside
install -d %{buildroot}%{installdir}/cache/lookaside/pkgs
install -d %{buildroot}%{installdir}/web

cp -a scripts/httpd/upload.cgi %{buildroot}%{installdir}/web/

%if 0%{?rhel} && 0%{?rhel} < 8
    sed -i '1 s|#.*|#!/usr/bin/python2|' %{buildroot}%{installdir}/web/upload.cgi
%endif

# ------------------------------------------------------------------------------
# /usr/bin/ ...... links to executable files
# ------------------------------------------------------------------------------
install -d %{buildroot}%{_bindir}
ln -s %{_datadir}/dist-git/setup_git_package %{buildroot}%{_bindir}/setup_git_package
ln -s %{_datadir}/dist-git/mkbranch %{buildroot}%{_bindir}/mkbranch
ln -s %{_datadir}/dist-git/mkbranch_branching %{buildroot}%{_bindir}/mkbranch_branching
ln -s %{_datadir}/dist-git/remove_unused_sources %{buildroot}%{_bindir}/remove_unused_sources

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

hardlink -cv %{buildroot}%{_datadir}/selinux

%post selinux
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp &> /dev/null || :
done
%{_sbindir}/restorecon -v %{installdir}/cache || :
%{_sbindir}/restorecon -v %{installdir}/cache/lookaside || :
%{_sbindir}/restorecon -v %{installdir}/cache/lookaside/pkgs || :
%{_sbindir}/restorecon -v %{installdir}/git || :
%{_sbindir}/restorecon -Rv %{installdir}/web/ || :

%systemd_post dist-git.socket

%preun
%systemd_preun dist-git.socket

%postun selinux
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}
  do
     /usr/sbin/semodule -s ${selinuxvariant} -r %{modulename} &> /dev/null || :
  done
fi

%systemd_postun dist-git.socket


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
%dir                   %{_sysconfdir}/httpd/conf.d/dist-git
%config(noreplace)     %{_sysconfdir}/httpd/conf.d/dist-git/*
%config(noreplace)     %{_sysconfdir}/httpd/conf.d/dist-git.conf

%{_unitdir}/dist-git@.service
%{_unitdir}/dist-git.socket

# ------------------------------------------------------------------------------
# /var/lib/ ...... dynamic persistent files
# ------------------------------------------------------------------------------

# non-standard-dir-perm:
# - git repositories and their contents must have w permission for their creators
%dir                              %{installdir}
%attr (2775, -, packager)         %{installdir}/git
%dir                              %{installdir}/web
%attr (755, apache, apache)       %{installdir}/web/upload.cgi
%dir                              %{installdir}/cache
%dir                              %{installdir}/cache/lookaside
%attr (2775, apache, apache)      %{installdir}/cache/lookaside/pkgs

# ------------------------------------------------------------------------------
# /usr/share ...... executable files
# ------------------------------------------------------------------------------

%dir              %{_datadir}/dist-git
%attr (775, -, -) %{_datadir}/dist-git/*


%files selinux
%doc selinux/*
%{_datadir}/selinux/*/%{modulename}.pp
%{_bindir}/*

%changelog
* Tue May 28 2019 Miroslav Suchy <msuchy@redhat.com> - 1.12-1
- remove old changelog entries
- do not specify full path for hardlink [RHBZ#1714637]
- add script for removing unused source tarballs in lookaside cache

* Tue Apr 30 2019 clime <clime@redhat.com> 1.11-1
- remove python3-configparser require
- move scripts to bindir

* Mon Mar 11 2019 clime <clime@redhat.com> 1.10-1
- python3 support
- fix post-receive hook in case post.receive.d is empty

* Fri Nov 23 2018 clime <clime@redhat.com> 1.9-1
- do not create sources file when creating a repo
- set umask 0002 in all available dist-git scripts
- Use REMOTE_USER as fallback for GSS_NAME
- add support for setting mtime for an uploaded file

* Tue Aug 14 2018 clime <clime@redhat.com> 1.8-1
- add disable group check option
- add lookaside_dir option
- deprecate cache_dir
- fix python-grokmirror dep

* Mon Feb 26 2018 clime <clime@redhat.com> 1.7-1
- move 'fedmsgs', 'old_paths', 'nomd5' options to optional upload section

* Mon Feb 19 2018 clime <clime@redhat.com> 1.6-1
- add 'fedmsgs', 'old_paths', and 'default_namespace' config options
- remove domain_read_all_domains_state SELinux rule
- require dist-git-selinux
- give optional map permission to git_system_t on git_user_content_t
- update requires to work for all environments
- make the package completely distribution-agnostic

* Mon Dec 18 2017 clime <clime@redhat.com> 1.5-1
- make selinux policy build on f27+
- add optional map SELinux permission for httpd_t

* Tue Jul 25 2017 clime <clime@redhat.com> 1.4-1
- disable md5 uploading by default

* Mon Jun 26 2017 clime <clime@redhat.com> 1.3-1
- translate '/' to '-' in package name for mailinglist hook
  (graybrandon@gmail.com)

* Fri May 26 2017 clime <clime@redhat.com> 1.2-1
- remove mail git hook
- grokmirror support

* Wed May 03 2017 clime <clime@redhat.com> 1.1-1
- fix default config value for email
- fix name/email switch

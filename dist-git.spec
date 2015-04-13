Name:		dist-git
Version:	0.4
Release:	1%{?dist}
Summary:	Package source version control system

Group:		Applications/Productivity
License:	gpl
URL:		none
Source0:	%{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  systemd

Requires:	httpd
Requires:	gitolite3
Requires:	perl-Sys-Syslog
Requires:	git-daemon
Requires:	python-requests
Requires:	/usr/sbin/semanage
Requires:       mod_ssl
Requires(pre):  shadow-utils

%description
Lorem ipsum dolor sit amet


%prep
%setup -q


%build



%pre
getent group packager > /dev/null || \
    groupadd -r packager

getent group gen-acls > /dev/null || \
    groupadd -r gen-acls

getent passed gen-acls > /dev/null || \
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
install -d %{buildroot}%{_sharedstatedir}/dist-git/git/rpms
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/conf
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/logs
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/local/VREF
install -d %{buildroot}%{_sharedstatedir}/dist-git/gitolite/hooks/common/update
install -d %{buildroot}%{_sharedstatedir}/dist-git/cache/lookaside/pkgs
install -d %{buildroot}%{_sharedstatedir}/dist-git/web

cp -a scripts/httpd/upload.cgi %{buildroot}%{_sharedstatedir}/dist-git/web/

ln -f -s %{_sysconfdir}/dist-git/gitolite.rc \
         %{buildroot}%{_sharedstatedir}/dist-git/git/.gitolite.rc

ln -f -s %{_sharedstatedir}/dist-git/gitolite \
         %{buildroot}%{_sharedstatedir}/dist-git/git/.gitolite

ln -f -s %{_sharedstatedir}/dist-git/git/rpms \
         %{buildroot}%{_sharedstatedir}/dist-git/git/repositories

ln -f -s %{_datadir}/git-core/update-block-push-origin \
         %{buildroot}%{_sharedstatedir}/dist-git/gitolite/local/VREF/update-block-push-origin



%files

# ------------------------------------------------------------------------------
# /usr/share/ .... static files
# ------------------------------------------------------------------------------
%attr (755, -, -) %{_datadir}/dist-git/*


# ------------------------------------------------------------------------------
# /etc/ .......... config files
# ------------------------------------------------------------------------------
%config     %{_sysconfdir}/dist-git/dist-git.conf
%config     %{_sysconfdir}/dist-git/gitolite.rc
%config     %{_sysconfdir}/httpd/conf.d/dist-git.conf
%config     %{_sysconfdir}/httpd/conf.d/ssl.conf.example
%config     %{_sysconfdir}/httpd/conf.d/dist-git/*
%config     %{_sysconfdir}/cron.d/dist-git/cgit_pkg_list.cron
%config     %{_sysconfdir}/cron.d/dist-git/dist_git_sync.cron
%config     %{_unitdir}/dist-git@.service
%config     %{_unitdir}/dist-git.socket


# ------------------------------------------------------------------------------
# /var/lib/ ...... dynamic persistent files
# ------------------------------------------------------------------------------
%attr (2775, -, packager)         %{_sharedstatedir}/dist-git/git/rpms
%attr (755, gen-acls, gen-acls)   %{_sharedstatedir}/dist-git/gitolite/conf
%attr (775, gen-acls, packager)   %{_sharedstatedir}/dist-git/gitolite/logs
%attr (775, gen-acls, packager)   %{_sharedstatedir}/dist-git/gitolite/local/VREF
%attr (770, -, packager)          %{_sharedstatedir}/dist-git/gitolite/hooks
%attr (770, -, packager)          %{_sharedstatedir}/dist-git/gitolite/hooks/common
%attr (755, -, packager)          %{_sharedstatedir}/dist-git/gitolite/hooks/common/update
%attr (755, apache, apache)       %{_sharedstatedir}/dist-git/web/upload.cgi
%attr (755, apache, apache)       %{_sharedstatedir}/dist-git/cache/lookaside/pkgs
%{_sharedstatedir}/dist-git/git/repositories
%{_sharedstatedir}/dist-git/git/.gitolite
%{_sharedstatedir}/dist-git/git/.gitolite.rc



%changelog
* Fri Apr 10 2015 Adam Samalik <asamalik@redhat.com> 0.4-1
- spec and config fix
- systemd services
* Tue Mar 31 2015 Adam Samalik <asamalik@redhat.com> 0.3-1
- alpha package (asamalik@redhat.com)

* Mon Mar 30 2015 Adam Samalik <asamalik@redhat.com> 0.2-1
- new package built with tito



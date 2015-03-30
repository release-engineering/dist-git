Name:		dist-git
Version:	0.2
Release:	1%{?dist}
Summary:	Package source version control system

Group:		Applications/Productivity
License:	gpl
URL:		none
Source0:	%{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:	httpd
Requires:	gitolite3
Requires:	cgit
Requires:	perl-Sys-Syslog
Requires:	git-daemon
Requires:	python-requests
Requires:	/usr/sbin/semanage

%description
Lorem ipsum dolor sit amet

# todo:
#   add group packager


%prep
%setup -q -c


%build



%install
install -d %{buildroot}%{_datadir}/dist-git
cp -a scripts/dist-git/* %{buildroot}%{_datadir}/dist-git/

install -d %{buildroot}%{_sysconfdir}/dist-git
cp -a configs/dist-git/dist-git.conf %{buildroot}%{_sysconfdir}/dist-git/

install -d %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git
cp -a configs/httpd/dist-git.conf %{buildroot}%{_sysconfdir}/httpd/
cp -a configs/httpd/ssl.conf %{buildroot}%{_sysconfdir}/httpd/
cp -a configs/httpd/dist-git/* %{buildroot}%{_sysconfdir}/httpd/conf.d/dist-git/

install -d %{buildroot}%{_sysconfdir}/cron.d/dist-git
cp -a configs/cron/* %{buildroot}%{_sysconfdir}/cron.d/dist-git/

install -d %{buildroot}%{_sharedstatedir}/dist-git/git/rpms
install -d %{buildroot}%{_sharedstatedir}/dist-git/cache/lookaside/pkgs
install -d %{buildroot}%{_sharedstatedir}/dist-git/web
cp -a scripts/httpd/upload.cgi %{buildroot}%{_sharedstatedir}/dist-git/web/

# FIXME: I can't override other configs!
cp -a configs/cgit/cgitrc %{buildroot}%{_sysconfdir}/

# FIXME: I can't override other configs!
cp -a configs/gitolite/gitolite.rc %{buildroot}%{_sysconfdir}/gitolite/

# FIXME: I can't override people's configs!
cp -a configs/systemd/git@.service %{buildroot}%{_libdir}/systemd/system/git@.service


%files
%dir %{_datadir}/dist-git
%attr (755, -, -) %{_datadir}/dist-git
%attr (755, -, -) %{_datadir}/dist-git/*

%dir %{_sysconfdir}/dist-git
%attr (755, -, -) %{_sysconfdir}/dist-git

%config(noreplace) %{_sysconfdir}/dist-git/dist-git.conf
%attr (755, -, -) %{_sysconfdir}/dist-git/dist-git.conf

%dir %{_sysconfdir}/httpd/conf.d/dist-git
%config(noreplace) %{_sysconfdir}/httpd/conf.d/dist-git.conf

%config(noreplace) %{_sysconfdir}/cron.d/dist-git/cgit_pkg_list.cron
%config(noreplace) %{_sysconfdir}/cron.d/dist-git/dist_git_sync.cron

%dir %{_sharedstatedir}/dist-git/git
%attr (755, -, -) %{_sharedstatedir}/dist-git/git

%dir %{_sharedstatedir}/dist-git/git/rpms
%attr (2775, -, packager) %{_sharedstatedir}/dist-git/git/rpms

%dir %{_sharedstatedir}/dist-git/cache/lookaside/pkgs
%attr (755, apache, apache) %{_sharedstatedir}/dist-git/cache/lookaside/pkgs

%dir %{_sharedstatedir}/dist-git/web
%attr (755, apache, apache) %{_sharedstatedir}/dist-git/web
%attr (755, apache, apache) %{_sharedstatedir}/dist-git/web/upload.cgi



%changelog
* Mon Mar 30 2015 Adam Samalik <asamalik@redhat.com> 0.2-1
- new package built with tito



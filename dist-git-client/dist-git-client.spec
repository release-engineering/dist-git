Name:      dist-git-client
Version:   1.0
Release:   2%{?dist}
Summary:   Get sources for RPM builds from DistGit repositories
BuildArch: noarch

License: GPL-2.0-or-later
URL:     https://github.com/release-engineering/dist-git.git

# Source is created by
# git clone https://github.com/release-engineering/dist-git.git
# cd dist-git-client
# tito build --tgz
Source0: %{name}-%{version}.tar.gz

Requires: curl
Requires: /usr/bin/git

BuildRequires: python3-devel
BuildRequires: python3-pytest
BuildRequires: python3-rpm-macros
BuildRequires: /usr/bin/argparse-manpage
BuildRequires: /usr/bin/git

%if 0%{?fedora} || 0%{?rhel} > 9
Requires: python3-rpmautospec
BuildRequires: python3-rpmautospec
%endif


%description
A simple, configurable python utility that is able to clone package sources from
a DistGit repository, download sources from the corresponding lookaside cache
locations, and generate source RPMs.

The utility is able to automatically map the .git/config clone URL into the
corresponding DistGit instance configuration.


%prep
%setup -q


%build
argparse-manpage --pyfile dist_git_client.py \
    --function _get_argparser \
    --author "Copr Team" \
    --author-email "copr-team@redhat.com" \
    --url %url --project-name Copr \
> dist-git-client.1


%install
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_mandir}/man1
install -d %{buildroot}%{_sysconfdir}/dist-git-client
install -d %{buildroot}%{python3_sitelib}
install -p -m 755 bin/dist-git-client %{buildroot}%{_bindir}
install -p -m 644 etc/default.ini \
    %{buildroot}%{_sysconfdir}/dist-git-client
install -p -m 644 dist_git_client.py %{buildroot}%{python3_sitelib}
install -p -m 644 dist-git-client.1 %{buildroot}%{_mandir}/man1/


%check
PYTHON=python3 ./run_tests.sh -vv --no-coverage


%files
%license LICENSE
%doc README.md
%{_bindir}/dist-git-client
%{_mandir}/man1/dist-git-client.1*
%dir %{_sysconfdir}/dist-git-client
%config(noreplace) %{_sysconfdir}/dist-git-client/default.ini
%{python3_sitelib}/dist_git_client.*
%{python3_sitelib}/__pycache__/dist_git_client*


%changelog
* Fri Jun 21 2024 Pavel Raiskup <praiskup@redhat.com> - 1.0-2
- Fedora Review fixes (rhbz#2293067)

* Thu Jun 06 2024 Pavel Raiskup <praiskup@redhat.com> - 1.0-1
- new package built with tito

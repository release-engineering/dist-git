#!/bin/bash

. /usr/bin/rhts-environment.sh || exit 1
. /usr/share/beakerlib/beakerlib.sh || exit 1

export TESTPATH="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function pkgs_cmd {
	ssh clime@pkgs.example.org $1
}

rlJournalStart
    rlPhaseStartSetup BasicTest
		pkgs_cmd 'git config --global user.email "clime@redhat.com"' # todo: add this to setup?
		pkgs_cmd 'git config --global user.name "clime"' # todo: add this to setup?
        pkgs_cmd 'setup_git_package prunerepo'
    rlPhaseEnd

    rlPhaseStartTest BasicTest
        CWD=`pwd`

        cd $TESTPATH

        # clone repo using fedpkg
        rlRun "fedpkg clone /var/lib/dist-git/git/repositories/prunerepo"

        cd prunerepo

        # upload into lookaside and working tree update
        rlRun "fedpkg import --skip-diffs ../prunerepo-1.1-1.fc23.src.rpm"

        # test of presence of the uploaded file
        rlRun 'wget http://pkgs.example.org/repo/pkgs/prunerepo/prunerepo-1.1.tar.gz/md5/c5af09c7fb2c05e556898c93c62b1e35/prunerepo-1.1.tar.gz'

        # commit of spec and updated sources and push into the git repo
        rlRun "git add -A && git commit -m 'test commit'"
        rlRun "git push"

        # get srpm file using fedpkg
        rlRun 'fedpkg --dist f25 srpm'

        cd ..

        # test git-daemon and git-http-backend by read access
        rlRun "git clone git://pkgs.example.org/prunerepo.git prunerepo-copy"
        rlRun "git clone http://pkgs.example.org/git/prunerepo prunerepo-copy2"

        cd $CWD
    rlPhaseEnd

    rlPhaseStartCleanup BasicTest
        rm -rf $TESTPATH/prunerepo $TESTPATH/prunerepo-copy* $TESTPATH/prunerepo-1.1.tar.gz
        pkgs_cmd 'rm -rf /var/lib/dist-git/git/repositories/prunerepo.git'
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/prunerepo'
    rlPhaseEnd
rlJournalEnd &> /dev/null

#!/bin/bash

. /usr/bin/rhts-environment.sh || exit 1
. /usr/share/beakerlib/beakerlib.sh || exit 1

export SCRIPTDIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export CWD=`pwd`
export TEST_CWD=`mktemp -d`

function pkgs_cmd {
	ssh  -o 'StrictHostKeyChecking no' clime@pkgs.example.org $1
}

rlJournalStart
    rlPhaseStartSetup rhpkgTest
        scp  -o 'StrictHostKeyChecking no' $SCRIPTDIR/dist-git.conf root@pkgs.example.org:/etc/dist-git/dist-git.conf
        pkgs_cmd 'git config --global user.email "clime@redhat.com"'
        pkgs_cmd 'git config --global user.name "clime"'
        pkgs_cmd '/usr/share/dist-git/setup_git_package rpms/prunerepo'
    rlPhaseEnd

    rlPhaseStartTest rhpkgTest
        cd $TEST_CWD
        echo "Running tests in $TEST_CWD"

        # clone repo using rhpkg
        rlRun "rhpkg -v clone rpms/prunerepo"

        cd prunerepo
        git config user.email "somebody@example.com"
        git config user.name "Some name"

        # upload into lookaside and working tree update
        rlRun "rhpkg -v import --skip-diffs $SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"

        # test of presence of the uploaded file
        rlRun 'wget http://pkgs.example.org/repo/pkgs/rpms/prunerepo/prunerepo-1.1.tar.gz/c5af09c7fb2c05e556898c93c62b1e35/prunerepo-1.1.tar.gz'

        # commit of spec and updated sources and push into the git repo
        rlRun "git add -A && git commit -m 'test commit'"
        rlRun "rhpkg push"

        # delete imported tarball
        rm prunerepo-1.1.tar.gz

        # get srpm file using rhpkg
        rlRun "rhpkg -v --release rhel-8 srpm"

        cd $CWD
    rlPhaseEnd

    rlPhaseStartCleanup rhpkgTest
        pkgs_cmd 'rm -rf /var/lib/dist-git/git/rpms/prunerepo.git'
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/rpms/prunerepo'
        rm -rf $TEST_CWD
    rlPhaseEnd
rlJournalEnd &> /dev/null

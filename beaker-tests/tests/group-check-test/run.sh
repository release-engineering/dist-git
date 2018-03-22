#!/bin/bash

. /usr/bin/rhts-environment.sh || exit 1
. /usr/share/beakerlib/beakerlib.sh || exit 1

export SCRIPTDIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export CWD=`pwd`
export TEST_CWD=`mktemp -d`

function pkgs_cmd {
	ssh  -o 'StrictHostKeyChecking no' clime@pkgs.example.org $1
}

function pkgs_root_cmd {
	ssh  -o 'StrictHostKeyChecking no' root@pkgs.example.org $1
}

rlJournalStart
    rlPhaseStartSetup DirectTest
        pkgs_root_cmd "gpasswd -a clime packager"
    rlPhaseEnd

    rlPhaseStartTest DirectTest
        cd $TEST_CWD
        echo "Running tests in $TEST_CWD"

        ### DISABLE_GROUP_CHECK = False
        pkgs_root_cmd "gpasswd -a clime packager"
        scp -o 'StrictHostKeyChecking no' $SCRIPTDIR/dist-git-group-check-on.conf root@pkgs.example.org:/etc/dist-git/dist-git.conf

        pkgs_root_cmd "gpasswd -d clime packager"
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi`
        rlRun "grep -q 'You must connect with a valid certificate and be in the packager group to upload.' <<< '$resp'"

        pkgs_root_cmd "gpasswd -a clime packager"
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi`
        rlRun "grep -q 'Required field \"name\" is not present.' <<< '$resp'"

        ### DISABLE_GROUP_CHECK = True
        pkgs_root_cmd "gpasswd -a clime packager"
        scp -o 'StrictHostKeyChecking no' $SCRIPTDIR/dist-git-group-check-off.conf root@pkgs.example.org:/etc/dist-git/dist-git.conf

        pkgs_root_cmd "gpasswd -d clime packager"
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi`
        rlRun "grep -q 'Required field \"name\" is not present.' <<< '$resp'"

        pkgs_root_cmd "gpasswd -a clime packager"
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi`
        rlRun "grep -q 'Required field \"name\" is not present.' <<< '$resp'"

        ### DISABLE_GROUP_CHECK unset
        pkgs_root_cmd "gpasswd -a clime packager"
        scp -o 'StrictHostKeyChecking no' $SCRIPTDIR/dist-git-group-check-unset.conf root@pkgs.example.org:/etc/dist-git/dist-git.conf

        pkgs_root_cmd "gpasswd -d clime packager"
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi`
        rlRun "grep -q 'You must connect with a valid certificate and be in the packager group to upload.' <<< '$resp'"

        pkgs_root_cmd "gpasswd -a clime packager"
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi`
        rlRun "grep -q 'Required field \"name\" is not present.' <<< '$resp'"

        cd $CWD
    rlPhaseEnd

    rlPhaseStartCleanup DirectTest
        rm -rf $TEST_CWD
    rlPhaseEnd
rlJournalEnd &> /dev/null

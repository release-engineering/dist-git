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
    rlPhaseStartSetup DirectTest
    rlPhaseEnd

    rlPhaseStartTest DirectTest
        cd $TEST_CWD
        echo "Running tests in $TEST_CWD"

        pkgs_cmd '/usr/share/dist-git/setup_git_package prunerepo'
        rlRun "git clone git://pkgs.example.org/rpms/prunerepo.git"

        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi`
        rlRun "grep -q 'Required field \"name\" is not present.' <<< '$resp'"

        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=prunerepo -F sha512sum=a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"`
        rlRun "grep -q 'stored OK' <<< '$resp'"

        # test of presence of the uploaded file
        rlRun 'wget http://pkgs.example.org/repo/pkgs/rpms/prunerepo/prunerepo-1.1-1.fc23.src.rpm/sha512/a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3/prunerepo-1.1-1.fc23.src.rpm'

        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=prunerepo -F sha512sum=a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3 -F filename=prunerepo-1.1-1.fc23.src.rpm`
        rlRun "grep -q 'Available' <<< '$resp'"

        # test that md5 is forbidden by default
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=foo -F md5sum=80e541f050d558424d62743195481595 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"`
        rlRun "grep -q 'Uploads with md5 are no longer allowed.' <<< '$resp'"

        cd $CWD
    rlPhaseEnd

    rlPhaseStartCleanup DirectTest
        pkgs_cmd 'rm -rf /var/lib/dist-git/git/rpms/prunerepo.git'
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/rpms/prunerepo'
        rm -rf $TEST_CWD
    rlPhaseEnd
rlJournalEnd &> /dev/null

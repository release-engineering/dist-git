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
         scp  -o 'StrictHostKeyChecking no' $SCRIPTDIR/dist-git.conf root@pkgs.example.org:/etc/dist-git/dist-git.conf
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

        # test an error is raised on a non-existing module
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=foo -F md5sum=80e541f050d558424d62743195481595 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"`
        rlRun "grep -q 'Module \"rpms/foo\" does not exist!' <<< '$resp'"

        # test that md5 is forbidden by default
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=prunerepo -F md5sum=80e541f050d558424d62743195481595 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"`
        rlRun "grep -q 'Uploads with md5 are no longer allowed.' <<< '$resp'"

        ### try operating without default namespacing
        scp -o 'StrictHostKeyChecking no' $SCRIPTDIR/dist-git-no-namespace.conf root@pkgs.example.org:/etc/dist-git/dist-git.conf

        pkgs_cmd '/usr/share/dist-git/setup_git_package prunerepo'
        rlRun "git clone git://pkgs.example.org/prunerepo.git prunerepo2"

        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=prunerepo -F sha512sum=a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"`
        rlRun "grep -q 'stored OK' <<< '$resp'"

        # test of presence of the uploaded file
        rlRun 'wget http://pkgs.example.org/repo/pkgs/prunerepo/prunerepo-1.1-1.fc23.src.rpm/sha512/a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3/prunerepo-1.1-1.fc23.src.rpm'

        # test an error is raised on a non-existing module
        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=foo -F md5sum=80e541f050d558424d62743195481595 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"`
        rlRun "grep -q 'Module \"foo\" does not exist!' <<< '$resp'"

        # test that mtime timestamp is preserved if sent
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/prunerepo'

        resp=`curl --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=prunerepo -F sha512sum=a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm" -F mtime=1234`
        rlRun "grep -q 'stored OK' <<< '$resp'"

        mtime_verbose=`curl -s --head http://pkgs.example.org/repo/pkgs/prunerepo/prunerepo-1.1-1.fc23.src.rpm/sha512/a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3/prunerepo-1.1-1.fc23.src.rpm | grep 'Last-Modified:' | sed -E 's/^Last-Modified:\s*(.*)/\1/'`
        mtime=`date +%s --date="$mtime_verbose"`
        rlAssertEquals "Verify that we got the correct timestamp back" $mtime 1234

        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/prunerepo'

        # Invalid mtime value returns 400 Bad Request
        code=`curl -w '%{response_code}' --output /dev/null --silent -X POST http://pkgs.example.org/repo/pkgs/upload.cgi -F name=prunerepo -F sha512sum=a5f31ae7586dae8dc1ca9a91df208893a0c3ab0032ab153c12eb4255f7219e4baec4c7581f353295c52522fee155c64f1649319044fd1bbb40451f123496b6b3 -F file=@"$SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm" -F mtime=invalid`
        rlAssertEquals "Verify that we got 400 error on invalid mtime value" $code 400

        cd $CWD
    rlPhaseEnd

    rlPhaseStartCleanup DirectTest
        pkgs_cmd 'rm -rf /var/lib/dist-git/git/rpms/prunerepo.git'
        pkgs_cmd 'rm -rf /var/lib/dist-git/git/prunerepo.git'
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/rpms/prunerepo'
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/prunerepo'
        rm -rf $TEST_CWD
    rlPhaseEnd
rlJournalEnd &> /dev/null

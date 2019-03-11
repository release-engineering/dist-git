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
    rlPhaseStartSetup BasicTest
        scp  -o 'StrictHostKeyChecking no' $SCRIPTDIR/dist-git.conf root@pkgs.example.org:/etc/dist-git/dist-git.conf
        pkgs_cmd 'git config --global user.email "clime@redhat.com"'
        pkgs_cmd 'git config --global user.name "clime"'
        pkgs_cmd '/usr/share/dist-git/setup_git_package rpms/prunerepo'
    rlPhaseEnd

    rlPhaseStartTest BasicTest
        cd $TEST_CWD
        echo "Running tests in $TEST_CWD"

        # clone repo using rpkg
        rlRun "rpkg -v clone rpms/prunerepo"

        cd prunerepo
        git config user.email "somebody@example.com"
        git config user.name "Some name"

        # upload into lookaside and working tree update
        rlRun "rpkg -v import --skip-diffs $SCRIPTDIR/../../data/prunerepo-1.1-1.fc23.src.rpm"

        # test of presence of the uploaded file
        rlRun 'wget http://pkgs.example.org/repo/pkgs/rpms/prunerepo/prunerepo-1.1.tar.gz/sha512/6a6a30c0e8c661176ba0cf7e8f1909a493a298fd5088389f5eb630b577dee157106e5f89dc429bcf2a6fdffe4bc10b498906b9746220882827560bc5f72a1b01/prunerepo-1.1.tar.gz'

        # commit of spec and updated sources and push into the git repo
        rlRun "git add -A && git commit -m 'test commit'"
        rlRun "rpkg push"

        # https://pagure.io/rpkg-client/issue/4
        rlRun "rpkg clean -x"

        # get srpm file using rpkg
        rlRun "rpkg srpm"

        cd ..

        # test git-daemon and git-http-backend by read access
        rlRun "git clone git://pkgs.example.org/rpms/prunerepo.git prunerepo-copy"
        rlRun "git clone http://pkgs.example.org/git/rpms/prunerepo prunerepo-copy2"

        # test manifest file update
        rlRun "wget http://pkgs.example.org/manifest.js.gz"
        gunzip ./manifest.js.gz
        rlRun "cat manifest.js | grep prunerepo.git"
        mv ./manifest.js manifest.js.prev

        # clone repo using rpkg
        rlRun "rpkg clone rpms/prunerepo prunerepo2"

        cd prunerepo2
        echo "manifest test" > sources

        rlRun "git add -A && git commit -m 'test commit 2'"
        rlRun "git push"

        cd ..

        rlRun "wget http://pkgs.example.org/manifest.js.gz"
        gunzip ./manifest.js.gz
        rlRun "cat manifest.js | grep prunerepo.git"

        modified_prev=`jq '.["/rpms/prunerepo.git"].modified' manifest.js.prev`
        modified=`jq '.["/rpms/prunerepo.git"].modified' manifest.js`

        rlAssertGreater "Check that 'modified' timestamp has been updated in the manifest file" $modified $modified_prev

        cd $CWD
    rlPhaseEnd

    rlPhaseStartCleanup BasicTest
        pkgs_cmd 'rm -rf /var/lib/dist-git/git/rpms/prunerepo.git'
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/rpms/prunerepo'
        rm -rf $TEST_CWD
    rlPhaseEnd
rlJournalEnd &> /dev/null

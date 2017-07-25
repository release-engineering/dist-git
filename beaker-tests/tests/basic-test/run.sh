#!/bin/bash

. /usr/bin/rhts-environment.sh || exit 1
. /usr/share/beakerlib/beakerlib.sh || exit 1

export TESTPATH="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function pkgs_cmd {
	ssh  -o 'StrictHostKeyChecking no' clime@pkgs.example.org $1
}

rlJournalStart
    rlPhaseStartSetup BasicTest
        pkgs_cmd 'git config --global user.email "clime@redhat.com"'
        pkgs_cmd 'git config --global user.name "clime"'
        pkgs_cmd '/usr/share/dist-git/setup_git_package prunerepo'
    rlPhaseEnd

    rlPhaseStartTest BasicTest
        CWD=`pwd`

        cd $TESTPATH

        # clone repo using fedpkg
        rlRun "fedpkg clone /var/lib/dist-git/git/prunerepo"

        cd prunerepo
        git config user.email "somebody@example.com"
        git config user.name "Some name"

        # upload into lookaside and working tree update
        rlRun "fedpkg import --skip-diffs ../prunerepo-1.1-1.fc23.src.rpm"

        # test of presence of the uploaded file
        rlRun 'wget http://pkgs.example.org/repo/pkgs/prunerepo/prunerepo-1.1.tar.gz/sha512/6a6a30c0e8c661176ba0cf7e8f1909a493a298fd5088389f5eb630b577dee157106e5f89dc429bcf2a6fdffe4bc10b498906b9746220882827560bc5f72a1b01/prunerepo-1.1.tar.gz'

        # commit of spec and updated sources and push into the git repo
        rlRun "git add -A && git commit -m 'test commit'"
        rlRun "git push"

        # get srpm file using fedpkg
        rlRun "fedpkg --dist f25 srpm"

        cd ..

        # test git-daemon and git-http-backend by read access
        rlRun "git clone git://pkgs.example.org/prunerepo.git prunerepo-copy"
        rlRun "git clone http://pkgs.example.org/git/prunerepo prunerepo-copy2"

        # test manifest file update
        rlRun "wget http://pkgs.example.org/manifest.js.gz"
        gunzip ./manifest.js.gz
        rlRun "cat manifest.js | grep prunerepo.git"
        mv ./manifest.js manifest.js.prev

        # clone repo using fedpkg
        rlRun "fedpkg clone /var/lib/dist-git/git/prunerepo prunerepo2"

        cd prunerepo2
        echo "manifest test" > sources

        rlRun "git add -A && git commit -m 'test commit 2'"
        rlRun "git push"

        cd ..

        rlRun "wget http://pkgs.example.org/manifest.js.gz"
        gunzip ./manifest.js.gz
        rlRun "cat manifest.js | grep prunerepo.git"

        modified_prev=`jq '.["/prunerepo.git"].modified' manifest.js.prev`
        modified=`jq '.["/prunerepo.git"].modified' manifest.js`

        rlAssertGreater "Check that 'modifed' timestamp has been updated in the manifest file" $modified $modified_prev

        cd $CWD
    rlPhaseEnd

    rlPhaseStartCleanup BasicTest
        rm -rf $TESTPATH/prunerepo $TESTPATH/prunerepo-copy* $TESTPATH/prunerepo2 $TESTPATH/prunerepo-1.1.tar.gz $TESTPATH/manifest*
        pkgs_cmd 'rm -rf /var/lib/dist-git/git/prunerepo.git'
        pkgs_cmd 'sudo rm -rf /var/lib/dist-git/cache/lookaside/pkgs/prunerepo'
    rlPhaseEnd
rlJournalEnd &> /dev/null

#!/bin/bash

. /usr/bin/rhts-environment.sh || exit 1
. /usr/share/beakerlib/beakerlib.sh || exit 1

export TESTPATH="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

rlJournalStart
    rlPhaseStartSetup BasicTest
        ssh clime@pkgs.fedoraproject.org 'setup_git_package prunerepo'
    rlPhaseEnd

    rlPhaseStartTest BasicTest
        cd $TESTPATH

        # clone repo using fedpkg
        rlRun "fedpkg clone /srv/git/repositories/prunerepo"

        cd prunerepo

        # upload into lookaside and working tree update
        rlRun "fedpkg import --skip-diffs ../prunerepo-1.1-1.fc23.src.rpm"

        # commit of spec and updated sources and push into the git repo
        rlRun "git add -A && git commit -m 'test commit'"
        rlRun "git push"

        cd ..

        # test git-daemon and git-http-backend by read access
        rlRun "git clone git://pkgs.fedoraproject.org/prunerepo.git prunerepo-copy"
        rlRun "git clone http://pkgs.fedoraproject.org/git/prunerepo prunerepo-copy2"

        # test of presence of the uploaded file
        rlRun 'wget http://pkgs.fedoraproject.org/repo/pkgs/prunerepo/prunerepo-1.1.tar.gz/sha512/6a6a30c0e8c661176ba0cf7e8f1909a493a298fd5088389f5eb630b577dee157106e5f89dc429bcf2a6fdffe4bc10b498906b9746220882827560bc5f72a1b01/prunerepo-1.1.tar.gz'

        cd -
    rlPhaseEnd

    rlPhaseStartCleanup BasicTest
        rm -rf $TESTPATH/prunerepo $TESTPATH/prunerepo-copy* $TESTPATH/prunerepo-1.1.tar.gz
        ssh clime@pkgs.fedoraproject.org 'rm -rf /srv/git/repositories/prunerepo.git'
    rlPhaseEnd
rlJournalEnd &> /dev/null

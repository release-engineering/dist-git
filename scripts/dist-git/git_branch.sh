#!/bin/bash
#
# Create a new development branch for a module.
# THIS HAS TO BE RUN ON THE GIT SERVER!

# WARNING:
# This file is maintained within puppet?
# All local changes will be lost.


# Figure out the environment we're running in
RUNDIR=$(cd $(dirname $0) && pwd)
GITROOT=/var/lib/dist-git/git/rpms

# check if a moron is driving me
if [ ! -d $GITROOT ] ; then
    # we're not on the git server (this check is fragile)
    echo "ERROR: This script has to be run on the git server."
    echo "ERROR: Homer sez 'Duh'."
    exit -9
fi

# where are the packages kept
TOPLEVEL=rpms

# Local variables
VERBOSE=0
TEST=
IGNORE=
BRANCH=""
PACKAGES=""
SRC_BRANCH="master"

Usage() {
    cat <<EOF
Usage:
    $0 [ -s <src_branch>] <branch> <package_name>...

    Creates a new branch <branch> for the list of <package_name>s.
    The /master suffix on branch names is assumed.

Options:
                                /master suffix on other branches assumed
    -n,--test           Don't do nothing, only test
    -i,--ignore                 Ignore erroneous modules
    -h,--help           This help message
    -v,--verbose        Increase verbosity
EOF
}

# parse the arguments
while [ -n "$1" ] ; do
    case "$1" in
    -h | --help )
        Usage
        exit 0
        ;;

    -v | --verbose )
        VERBOSE=$(($VERBOSE + 1))
        ;;

    -i | --ignore )
        IGNORE="yes"
        ;;

    -n | --test )
        TEST="yes"
        ;;


    -b | --branch )
        shift
        BRANCH=$1/master
        ;;

    --default-branch-author )
        shift
        AUTHOR=$1
        ;;

    * )
        if [ -z "$BRANCH" ] ; then
        BRANCH="$1"
        else
        PACKAGES="$PACKAGES $1"
        fi
        ;;
    esac
    shift
done

# check the arguments
if [ -z "$BRANCH" -o -z "$PACKAGES" ] ; then
    Usage
    exit -1
fi

if [ -z $AUTHOR ]; then
    AUTHOR=`crudini --get /etc/dist-git/dist-git.conf git default_branch_author`
fi


# Sanity checks before we start doing damage
NEWP=
for p in $PACKAGES ; do
    [ $VERBOSE -gt 1 ] && echo "Checking package $p..."
    if [ ! -d $GITROOT/$p.git ] ; then
    echo "ERROR: Package module $p is invalid" >&2
    [ "$IGNORE" = "yes" ] && continue || exit -1
    fi
    $(GIT_DIR=$GITROOT/$p.git git rev-parse -q --verify \
      $BRANCH >/dev/null) && \
    (echo "IGNORING: Package module $p already has a branch $BRANCH" >&2; \
    [ "$IGNORE" = "yes" ] && continue || exit -1)
    NEWP="$NEWP $p"
done
PACKAGES="$(echo $NEWP)"
if [ -z "$PACKAGES" ] ; then
    echo "NOOP: no valid packages found to process"
    exit -1
fi

if [ -n "$TEST" ] ; then
    echo "Branch $BRANCH valid for $PACKAGES"
    exit 0
fi

# "global" permissions check
if [ ! -w $GITROOT ] ; then
    echo "ERROR: You can not write to $GITROOT"
    echo "ERROR: You can not perform branching operations"
    exit -1
fi

# Now start working on creating those branches

# For every module, "create" the branch
for NAME in $PACKAGES ; do
    echo
    echo "Creating new module branch '$BRANCH' for '$NAME'..."

    # permissions checks for this particular module
    if [ ! -w $GITROOT/$NAME.git/refs/heads/  ] ; then
        echo "ERROR: You can not write to $d"
        echo "ERROR: $NAME can not be branched by you"
        continue
    fi
    ####  Replace the above with a gitolite permission check
    #[ $VERBOSE -gt 0 ] && echo "Creating $BRANCH-split tag for $NAME/$SRC_BRANCH..."
    # Is the above needed?
    #cvs -Q rtag -f "$BRANCH-split" $TOPLEVEL/$NAME/$SRC_BRANCH || {
    #echo "ERROR: Branch split tag for $NAME/$SRC_BRANCH could not be created" >&2
    #exit -2
    #}
    [ $VERBOSE -gt 0 ] && echo "Creating $NAME $BRANCH from $NAME ..."
    $(pushd $GITROOT/$NAME.git >/dev/null && \
    git branch --no-track $BRANCH `git rev-list --max-parents=0 master | head -1` && \
    popd >/dev/null) || {
    echo "ERROR: Branch $NAME $BRANCH could not be created" >&2
        popd >/dev/null
    exit -2
    }
done

echo
echo "Done."

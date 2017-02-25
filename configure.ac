AC_INIT([dist-git], [0.13], [msuchy@redhat.com])
AC_CONFIG_AUX_DIR([build_aux])
AC_CONFIG_MACRO_DIR([m4])

AM_INIT_AUTOMAKE([-Wall foreign])
AM_SILENT_RULES([yes])

_AX_TEXT_TPL_INIT
_AX_TEXT_TPL_SUBST([ac_aux_dir])
_AX_TEXT_TPL_SUBST([distgit_confdir],           [${sysconfdir}/dist-git])
_AX_TEXT_TPL_SUBST([apache_confdir],            [${sysconfdir}/httpd/conf.d])
_AX_TEXT_TPL_SUBST([apache_conf_distgitdir],    [${apache_confdir}/dist-git])
# TODO!  CGI script should be somewhere else, this directory is overmounted!
_AX_TEXT_TPL_SUBST([webdir],                    [${localstatedir}/lib/dist-git/web])
_AX_TEXT_TPL_SUBST([systemd_unitsdir],          [${prefix}/lib/systemd/system])
_AX_TEXT_TPL_SUBST([selinuxmoduledir],          [${datadir}/selinux])

_AX_TEXT_TPL_SUBST([selinux_module],            [dist_git])
SELINUX_VARIANTS=
AC_ARG_WITH([selinux-variants],
            AS_HELP_STRING([--with-selinux-variants],
                           [Space separated list of SELinux variants to be built]),
            [SELINUX_VARIANTS=$withval])

sp=
for variant in $SELINUX_VARIANTS
do
    new_variants="$new_variants$sp$selinux_module.pp.$variant"
    sp=' '
done
SELINUX_VARIANTS=$new_variants

_AX_TEXT_TPL_SUBST([SELINUX_VARIANTS])

SHELL_PARSE_CONFIG="eval \$\$(crudini --format=sh --get ${distgit_confdir}/dist-git.conf)"
_AX_TEXT_TPL_SUBST([SHELL_PARSE_CONFIG])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT

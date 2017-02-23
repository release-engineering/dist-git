# Text templating system with autoconf
# ====================================
#
# Correctly generate files based on ./configure check results.  The @variable@
# substitution is usually done by config.status from *.in files, however
# substuing paths like @libexecdir@ can result into '${exec_prefix}/libexec'
# which is not desired for installed scripts, for example, where we need to have
# fully expanded paths.  The aim of this script is to generalize steps users
# usually do to perform full expansion of configure variables.  Currently we use
# sed substitution only.
#
# The easiest usage of this templating system is like this:
#   $ cat configure.ac | "grep interresting lines"
#   _AX_TEXT_TPL_INIT
#   some_other_var="some other var content"
#   _AX_TEXT_TPL_SUBST([some_other_var])
#
#   $ cat Makefile (or Makefile.am):
#   generated_file: TEMPLATE.in $(text_tpl_deps)
#   <<tab>>$(text_tpl_gen)
#
# Limitations:
# - this code is probably not terribly portable
# - substitutions should not contain '|' character (because we use sed rules
#   spelled like 's|||'), you can do things like '\|', however you need to
#   take into account that substitution done by 'sed' and by 'config.status' are
#   not the same.  Also be careful about escaping '\' caracter.
# - only single-line substitutions are expected;  you may use '\n' however
#   there is the same problem as with '|' and '\'.
#
# TODO:
# - we should do something similar to what config.status does (awk generated
#   source code for substitutions), however even thought usually variable
#   (macro) values are defined by ./configure, some may be defined like 'make
#   VARIABLE=VALUE'.

# sed_subst_var_pattern VARNAME (private macro)
# ---------------------------------------------
# Generate sed substitution rule to substitute @VARNAME@ with fully expaned
# value of $VARNAME.  The trick is that we use 'make' to expand the value.
# The VARNAME must be AC_SUBST'ed (and all its sub-components like ${prefix},
# etc.) to allow 'make' doing correct expansion.
m4_define([sed_subst_var_pattern], [\\
	-e 's|@$1[[@]]|\$($1)|g'])

# _AX_TEXT_TPL_INIT
# -----------------
# Initialize the templating system.
AC_DEFUN([_AX_TEXT_TPL_INIT], [

__ax_text_tpl_default_variables="\
    abs_builddir
    abs_srcdir
    abs_top_builddir
    abs_top_srcdir
    bindir
    build_alias
    builddir
    datarootdir
    datadir
    docdir
    dvidir
    exec_prefix
    host_alias
    htmldir
    includedir
    infodir
    libdir
    libexecdir
    localedir
    localstatedir
    mandir
    oldincludedir
    pdfdir
    pkgdatadir
    prefix
    psdir
    sbindir
    sharedstatedir
    srcdir
    sysconfdir
    target_alias
    top_srcdir
    PACKAGE
    PACKAGE_BUGREPORT
    PACKAGE_NAME
    PACKAGE_STRING
    PACKAGE_TARNAME
    PACKAGE_URL
    PACKAGE_VERSION
    PATH_SEPARATOR
    SHELL
    VERSION
"

__ax_text_tpl_sed_rules=""
for i in $__ax_text_tpl_default_variables
do
__ax_text_tpl_sed_rules="$__ax_text_tpl_sed_rules \
sed_subst_var_pattern($i)"
done

__ax_text_tpl_sed_rules="$__ax_text_tpl_sed_rules \\
	\$(__ax_text_tpl_user_sed_rules) \\
	\$(_AX_TEXT_ADDITIONAL_SED_SUBSTITUTIONS) \\
	\$\$ax_text_add_sed_substs \\
	-e 's|@__FILE__[[@]]|\@S|@@|g'"

__ax_text_tpl_sed_call="\$(SED) \$(__ax_text_tpl_sed_rules)"
text_tpl_sed_call=$__ax_text_tpl_sed_call
m4_pattern_allow(AM_V_GEN)

# Convenient snippet to clean & prepare for following build
text_tpl_gen_conv_verbose="rm -rf \@S|@@; \$(MKDIR_P) \$(@D)"
text_tpl_gen_conv="\$(AM_V_GEN)\$(text_tpl_gen_conv_verbose)"

# Instantiate arbitrary data text file
text_tpl_gen_verbose="\$(text_tpl_gen_conv_verbose) && \$(__ax_text_tpl_sed_call) \$< > \@S|@@ && chmod -w \@S|@@"
text_tpl_gen="\$(AM_V_GEN)\$(text_tpl_gen_verbose)"

# Instantiate script file
text_tpl_gen_script_verbose="\$(text_tpl_gen_verbose) && chmod +x \@S|@@"
text_tpl_gen_script="\$(AM_V_GEN)\$(text_tpl_gen_script_verbose) && chmod +x \@S|@@"

# Make dependencies for targets of $(text_tpl_gen) and $(text_tpl_gen_script)
text_tpl_deps='$(top_builddir)/config.status Makefile'

AC_PATH_PROG([SED], [sed])
test -z "$ac_cv_path_SED" &&
    AC_MSG_ERROR([Sed is needed but not found.])

AC_SUBST([__ax_text_tpl_sed_call])
AC_SUBST([__ax_text_tpl_sed_rules])
AC_SUBST([__ax_text_tpl_user_sed_rules])
AC_SUBST([text_tpl_deps])
AC_SUBST([text_tpl_sed_call])
AC_SUBST([text_tpl_gen])
AC_SUBST([text_tpl_gen_verbose])
AC_SUBST([text_tpl_gen_conv])
AC_SUBST([text_tpl_gen_conv_verbose])
AC_SUBST([text_tpl_gen_script])
AC_SUBST([text_tpl_gen_script_verbose])
])

# _AX_TEXT_TPL_SUBST SHELL_VARNAME [VALUE]
# ----------------------------------------
# Do substitution of SHELL_VARNAME both by config.status, and by sed call
# in instantiation rules.
AC_DEFUN([_AX_TEXT_TPL_SUBST], [
test x = x"$2" || $1=$2
__ax_text_tpl_user_sed_rules="$__ax_text_tpl_user_sed_rules\
sed_subst_var_pattern($1)"
AC_SUBST($1)
])


# _AX_TEXT_TPL_ARG_VAR VARNAME DEFAULT DESCRIPTION
# ------------------------------------------------
AC_DEFUN([_AX_TEXT_TPL_ARG_VAR], [
AC_ARG_VAR([$1], [$3])
test -z "$$1" && $1=$2
_AX_TEXT_TPL_SUBST($1)
])

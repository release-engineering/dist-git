CLEANFILES =
EXTRA_DIST = \
	COPYING \
	LICENSE \
	README.md \
	$(ac_aux_dir)/build-selinux-module \
	$(ac_aux_dir)/install-selinux-module.in

# Define some variables here so included makefiles can just '+='
pkgdata_SCRIPTS =
dist_libexec_SCRIPTS =

nodist_noinst_SCRIPTS = install-selinux-module
install-selinux-module: $(ac_aux_dir)/install-selinux-module.in $(text_tpl_deps)
	$(text_tpl_gen_script)

DISTCLEANFILES = install-selinux-module

include scripts/dist-git/Makefile.inc
include scripts/httpd/Makefile.inc
include configs/Makefile.inc
include selinux/Makefile.inc

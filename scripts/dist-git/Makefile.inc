pkgdata_SCRIPTS += \
	%D%/cgit_pkg_list \
	%D%/mkbranch \
	%D%/mkbranch_branching \
	%D%/setup_git_package

%D%/cgit_pkg_list: %D%/cgit_pkg_list.in $(text_tpl_deps)
	$(text_tpl_gen_script)

%D%/mkbranch: %D%/mkbranch.in $(text_tpl_deps)
	$(text_tpl_gen_script)

%D%/mkbranch_branching: %D%/mkbranch_branching.in $(text_tpl_deps)
	$(text_tpl_gen_script)

%D%/setup_git_package: %D%/setup_git_package.in $(text_tpl_deps)
	$(text_tpl_gen_script)

CLEANFILES += \
	$(pkgdata_SCRIPTS)

EXTRA_DIST += \
	%D%/cgit_pkg_list.in \
	%D%/mkbranch.in \
	%D%/mkbranch_branching.in \
	%D%/setup_git_package.in

web_SCRIPTS = %D%/upload.cgi

%D%/upload.cgi: %D%/upload.cgi.in $(text_tpl_deps)
	$(text_tpl_gen_script)

CLEANFILES += $(web_SCRIPTS)

EXTRA_DIST += %D%/upload.cgi.in

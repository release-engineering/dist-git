dist_distgit_conf_DATA = %D%/dist-git/dist-git.conf

dist_apache_conf_DATA = %D%/httpd/dist-git.conf

dist_apache_conf_distgit_DATA = \
	%D%/httpd/dist-git/git-smart-http.conf \
	%D%/httpd/dist-git/lookaside.conf

dist_systemd_units_DATA = \
	%D%/systemd/dist-git@.service \
	%D%/systemd/dist-git.socket

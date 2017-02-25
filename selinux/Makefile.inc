selinux_module = dist_git

selinux_source_files = \
	%D%/$(selinux_module).fc \
	%D%/$(selinux_module).te \
	%D%/$(selinux_module).if

EXTRA_DIST += $(selinux_source_files)

noinst_DATA = $(SELINUX_VARIANTS)

doc_DATA = \
	$(selinux_source_files)

install-data-hook:
	$(builddir)/install-selinux-module \
	  --destdir $(DESTDIR) \
	  -- $(SELINUX_VARIANTS)

uninstall-hook:
	$(builddir)/install-selinux-module \
	  --uninstall \
	  --destdir $(DESTDIR) \
	  -- $(SELINUX_VARIANTS)

# Parallel build causes issues here ATM
$(SELINUX_VARIANTS): $(selinux_source_files)
	$(AM_V_GEN)flock . $(ac_aux_dir)/build-selinux-module  $(selinux_module) $@ %D%

CLEANFILES += $(SELINUX_VARIANTS)

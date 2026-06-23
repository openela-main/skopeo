%global with_debug 1

%if 0%{?with_debug}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package %{nil}
%endif

%global gomodulesmode GO111MODULE=on

#%%global branch release-1.21
%global commit0 267465e170820673de25149378284fb352daa65e
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

# No btrfs on RHEL
%if %{defined fedora}
%define build_with_btrfs 1
%endif

%if %{defined rhel}
%define fips 1
%endif

# Only used in official koji builds
# Copr builds set a separate epoch for all environments
%if %{defined fedora}
%define conditional_epoch 1
%define fakeroot 1
%else
%define conditional_epoch 2
%endif

Name: skopeo
%if %{defined copr_username}
Epoch: 102
%else
Epoch: %{conditional_epoch}
%endif
# DO NOT TOUCH the Version string!
# The TRUE source of this specfile is:
# https://github.com/containers/skopeo/blob/main/rpm/skopeo.spec
# If that's what you're reading, Version must be 0, and will be updated by Packit for
# copr and koji builds.
# If you're reading this on dist-git, the version is automatically filled in by Packit.
Version: 1.22.2
# The `AND` needs to be uppercase in the License for SPDX compatibility
License: Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND ISC AND MIT AND MPL-2.0
Release: 6%{?dist}
%if %{defined golang_arches_future}
ExclusiveArch: %{golang_arches_future}
%else
ExclusiveArch: aarch64 ppc64le s390x x86_64
%endif
Summary: Inspect container images and repositories on registries
URL: https://github.com/containers/%{name}
# Tarball fetched from upstream
%if 0%{?branch:1}
Source0: https://github.com/containers/%{name}/tarball/%{commit0}/%{branch}-%{shortcommit0}.tar.gz
%else
Source0: https://github.com/containers/%{name}/archive/%{commit0}/%{name}-%{version}-%{shortcommit0}.tar.gz
%endif
BuildRequires: %{_bindir}/go-md2man
%if %{defined build_with_btrfs}
BuildRequires: btrfs-progs-devel
%endif
BuildRequires: git-core
BuildRequires: golang
%if !%{defined gobuild}
BuildRequires: go-rpm-macros
%endif
BuildRequires: gpgme-devel
BuildRequires: libassuan-devel
BuildRequires: glib2-devel
BuildRequires: make
BuildRequires: shadow-utils-subid-devel
BuildRequires: sqlite-devel
Requires: containers-common >= 4:1-21
%if %{defined sequoia}
Requires: podman-sequoia
%endif

%description
Command line utility to inspect images and repositories directly on Docker
registries without the need to pull them.

# NOTE: The tests subpackage is only intended for testing and will not be supported
# for end-users and/or customers.
%package tests
Summary: Test dependencies for %{name}

Requires: %{name} = %{epoch}:%{version}-%{release}
Requires: gnupg
Requires: jq
Requires: golang
Requires: podman
Requires: crun
Requires: httpd-tools
Requires: openssl
Requires: squashfs-tools
# bats and fakeroot are not present on RHEL and ELN so they shouldn't be strong deps
Recommends: bats
Recommends: fakeroot

%description tests
This package installs system test dependencies for %{name}

%prep
%if 0%{?branch:1}
%autosetup -Sgit -n containers-%{name}-%{shortcommit0}
%else
%autosetup -Sgit -n %{name}-%{commit0}
%endif
# The %%install stage should not rebuild anything but only install what's
# built in the %%build stage. So, remove any dependency on build targets.
sed -i 's/^install-binary: bin\/%{name}.*/install-binary:/' Makefile
sed -i 's/^completions: bin\/%{name}.*/completions:/' Makefile
sed -i 's/^install-docs: docs.*/install-docs:/' Makefile

%build
%set_build_flags
export CGO_CFLAGS=$CFLAGS

# These extra flags present in $CFLAGS have been skipped for now as they break the build
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-flto=auto//g')
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-Wp,D_GLIBCXX_ASSERTIONS//g')
CGO_CFLAGS=$(echo $CGO_CFLAGS | sed 's/-specs=\/usr\/lib\/rpm\/redhat\/redhat-annobin-cc1//g')

%ifarch x86_64
export CGO_CFLAGS="$CGO_CFLAGS -m64 -mtune=generic -fcf-protection=full"
%endif

BASEBUILDTAGS="$(hack/libsubid_tag.sh) libsqlite3"
%if %{defined build_with_btrfs}
export BUILDTAGS="$BASEBUILDTAGS $(hack/btrfs_installed_tag.sh)"
%else
export BUILDTAGS="$BASEBUILDTAGS exclude_graphdriver_btrfs"
%endif

%if %{defined fips}
export BUILDTAGS="$BUILDTAGS libtrust_openssl"
%endif

%if %{defined sequoia}
export BUILDTAGS="$BUILDTAGS containers_image_sequoia"
%endif

# unset LDFLAGS earlier set from set_build_flags
LDFLAGS=''

%gobuild -o bin/%{name} ./cmd/%{name}
%{__make} docs

%install
make \
    DESTDIR=%{buildroot} \
    PREFIX=%{_prefix} \
    install-binary install-docs install-completions

# system tests
install -d -p %{buildroot}/%{_datadir}/%{name}/test/system
cp -pav systemtest/* %{buildroot}/%{_datadir}/%{name}/test/system/

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

# Include this to silence rpmlint.
# Especially annoying if you use syntastic vim plugin.
%check

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_mandir}/man1/%{name}*
%dir %{_datadir}/bash-completion
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/%{name}
%dir %{_datadir}/fish/vendor_completions.d
%{_datadir}/fish/vendor_completions.d/%{name}.fish
%dir %{_datadir}/zsh/site-functions
%{_datadir}/zsh/site-functions/_%{name}

%files tests
%license LICENSE vendor/modules.txt
%{_datadir}/%{name}/test

%changelog
* Thu May 07 2026 Jindrich Novy <jnovy@redhat.com> - 1:1.22.2-6
- Rebuild for CVE-2026-32283
- Resolves: RHEL-167688

* Mon May 04 2026 Jindrich Novy <jnovy@redhat.com> - 1:1.22.2-5
- Rebuild for CVE-2026-25679
- Re-add test file installation to fix tier0 tests
- Resolves: RHEL-158789

* Wed Apr 15 2026 Jindrich Novy <jnovy@redhat.com> - 1:1.22.2-1
- update to https://github.com/containers/skopeo/releases/tag/v1.22.2
- fixes signature verification of images which only sign the per-platform
  manifest in skopeo proxy
- Resolves: RHEL-168166

* Mon Feb 23 2026 Jindrich Novy <jnovy@redhat.com> - 1:1.22.0-2
- Rebuild for new golang to address CVE-2025-68121
- Resolves: RHEL-149649

* Thu Feb 12 2026 Jindrich Novy <jnovy@redhat.com> - 1:1.22.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.22.0
- Related: RHEL-111919

* Wed Feb 04 2026 Jindrich Novy <jnovy@redhat.com> - 1:1.21.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.21.0
- Related: RHEL-111919

* Fri Nov 21 2025 Jindrich Novy <jnovy@redhat.com> - 1:1.20.0-2
- rebuild for CVE-2025-58183
- Resolves: RHEL-125721

* Mon Aug 11 2025 Jindrich Novy <jnovy@redhat.com> - 1:1.20.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.20.0
- Related: RHEL-80816

* Wed Jun 18 2025 Jindrich Novy <jnovy@redhat.com> - 1:1.19.0-2
- Do not require BATS on RHEL
- Resolves: RHEL-97592

* Tue Jun 10 2025 Jindrich Novy <jnovy@redhat.com> - 1:1.19.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.19.0
- Related: RHEL-80816

* Tue Mar 18 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.1-3
- fix gating.yaml
- Related: RHEL-80816

* Fri Mar 14 2025 Lokesh Mandvekar <lsm5@redhat.com> - 2:1.18.1-2
- Fix bats dep on tests subpackage
- Resolves: RHEL-80616

* Fri Mar 14 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.1-1
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.18
  (https://github.com/containers/skopeo/commit/bfd0850)
- fixes "CVE-2025-27144 skopeo: Go JOSE's Parsing Vulnerable to Denial of Service [rhel-9.7]"
- Resolves: RHEL-80616

* Thu Feb 13 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.0-2
- fix the broken condition introduced by upstream
- Related: RHEL-60277

* Thu Feb 13 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.18.0
- Related: RHEL-60277

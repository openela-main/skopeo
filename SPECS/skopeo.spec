%global with_debug 1

%if 0%{?with_debug}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package %{nil}
%endif

%global gomodulesmode GO111MODULE=on

%global branch release-1.18
%global commit0 bfd0850f067e79cf4a60a911e212a62bd55181fb
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

# No btrfs on RHEL
%if %{defined fedora}
%define build_with_btrfs 1
%endif

%if %{defined rhel}
%define fips 1
%endif

Name: skopeo
Epoch: 2
Version: 1.18.1
Release: 2%{?dist}
# The `AND` needs to be uppercase in the License for SPDX compatibility
License: Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND ISC AND MIT AND MPL-2.0
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
BuildRequires: ostree-devel
BuildRequires: glib2-devel
BuildRequires: make
BuildRequires: shadow-utils-subid-devel
Requires: containers-common

%description
Command line utility to inspect images and repositories directly on Docker
registries without the need to pull them

%package tests
Summary: Tests for %{name}

Requires: %{name} = %{epoch}:%{version}-%{release}
%if %{defined fedora}
Requires: bats
Requires: fakeroot
%endif
Requires: gnupg
Requires: jq
Requires: golang
Requires: podman
Requires: crun
Requires: httpd-tools
Requires: openssl
Requires: squashfs-tools

%description tests
%{summary}

This package contains system tests for %{name}

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

BASEBUILDTAGS="$(hack/libsubid_tag.sh)"
%if %{defined build_with_btrfs}
export BUILDTAGS="$BASEBUILDTAGS $(hack/btrfs_tag.sh) $(hack/btrfs_installed_tag.sh)"
%else
export BUILDTAGS="$BASEBUILDTAGS btrfs_noversion exclude_graphdriver_btrfs"
%endif

%if %{defined fips}
export BUILDTAGS="$BUILDTAGS libtrust_openssl"
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
* Wed Jun 04 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.1-2
- rebuild to fix CVE-2025-22871 skopeo: Request smuggling due to acceptance of invalid chunked data in net/http
- Resolves: RHEL-89329

* Mon Mar 17 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.1-1
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.18
  (https://github.com/containers/skopeo/commit/bfd0850)
- fixes "CVE-2025-27144 skopeo: Go JOSE's Parsing Vulnerable to Denial of Service [rhel-9.6.z]"
- Resolves: RHEL-82972

* Thu Feb 13 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.0-2
- fix the broken condition introduced by upstream
- Related: RHEL-60277

* Thu Feb 13 2025 Jindrich Novy <jnovy@redhat.com> - 2:1.18.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.18.0
- Related: RHEL-60277

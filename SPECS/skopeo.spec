%global with_check 0

%if 0%{?rhel} > 7 && ! 0%{?fedora}
%define gobuild(o:) \
go build -buildmode pie -compiler gc -tags="rpm_crashtraceback libtrust_openssl ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-} -compressdwarf=false -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags'" -a -v %{?**};
%else
%define gobuild(o:) GO111MODULE=off go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '-Wl,-z,relro -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld '" -a -v %{?**};
%endif

%global import_path github.com/containers/%{name}
%global branch release-1.14
%global commit0 5f2b9afebe813012e936cd5b3f4bae1caae8bd6f
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

Epoch: 2
Name: skopeo
Version: 1.14.3
Release: 3%{?dist}
Summary: Inspect container images and repositories on registries
License: ASL 2.0
URL: https://%{import_path}
# https://fedoraproject.org/wiki/PackagingDrafts/Go#Go_Language_Architectures
ExclusiveArch: %{go_arches}
%if 0%{?branch:1}
Source0: https://%{import_path}/tarball/%{commit0}/%{branch}-%{shortcommit0}.tar.gz
%else
Source0: https://%{import_path}/archive/%{commit0}/%{name}-%{version}-%{shortcommit0}.tar.gz
%endif
BuildRequires: git-core
BuildRequires: golang >= 1.20.10
BuildRequires: /usr/bin/go-md2man
BuildRequires: gpgme-devel
BuildRequires: libassuan-devel
BuildRequires: pkgconfig(devmapper)
BuildRequires: glib2-devel
BuildRequires: make
Requires: containers-common >= 2:1-2
Requires: system-release

%description
Command line utility to inspect images and repositories directly on Docker
registries without the need to pull them

%package tests
Summary: Tests for %{name}
Requires: %{name} = %{epoch}:%{version}-%{release}
#Requires: bats  (which RHEL8 doesn't have. If it ever does, un-comment this)
Requires: gnupg
Requires: jq
Requires: golang >= 1.20.10
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
sed -i 's/install-binary: bin\/%{name}/install-binary:/' Makefile
sed -i 's/completions: bin\/%{name}/completions:/' Makefile
sed -i 's/install-docs: docs/install-docs:/' Makefile

%build
mkdir -p src/github.com/containers
ln -s ../../../ src/%{import_path}

mkdir -p vendor/src
for v in vendor/*; do
    if test ${v} = vendor/src; then continue; fi
    if test -d ${v}; then
      mv ${v} vendor/src/
    fi
done

export GOPATH=$(pwd):$(pwd)/vendor
export GO111MODULE=off
export CGO_CFLAGS="%{optflags} -D_GNU_SOURCE -D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64"
export BUILDTAGS="exclude_graphdriver_btrfs btrfs_noversion $(hack/libdm_tag.sh)"
mkdir -p bin
%gobuild -o bin/%{name} ./cmd/%{name}
%{__make} docs

%install
make install-binary install-docs install-completions DESTDIR=%{buildroot} PREFIX=%{_prefix}

# system tests
install -d -p %{buildroot}/%{_datadir}/%{name}/test/system
cp -pav systemtest/* %{buildroot}/%{_datadir}/%{name}/test/system/

%check
%if 0%{?with_check}
export GOPATH=%{buildroot}/%{gopath}:$(pwd)/vendor:%{gopath}

%gotest %{import_path}/integration
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

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
%license LICENSE
%{_datadir}/%{name}/test

%changelog
* Fri Jun 21 2024 Jindrich Novy <jnovy@redhat.com> - 2:1.14.3-3
- rebuild for CVE-2024-1394
- Resolves: RHEL-24321

* Fri Apr 19 2024 Jindrich Novy <jnovy@redhat.com> - 2:1.14.3-2
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.14
  (https://github.com/containers/skopeo/commit/5f2b9af)
- Resolves: RHEL-28736

* Mon Apr 01 2024 Lokesh Mandvekar <lsm5@redhat.com> - 2:1.14.3-1
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.14
  (https://github.com/containers/skopeo/commit/4a2bc3a)
- Resolves: RHEL-28235

* Mon Mar 18 2024 Jindrich Novy <jnovy@redhat.com> - 2:1.14.3-0.2
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.14
  (https://github.com/containers/skopeo/commit/d0a0f1a)
- Resolves: RHEL-28235

* Fri Feb 02 2024 Jindrich Novy <jnovy@redhat.com> - 2:1.14.3-0.1
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.14
  (https://github.com/containers/skopeo/commit/1c2ab99)
- Related: RHEL-2112

* Wed Jan 31 2024 Jindrich Novy <jnovy@redhat.com> - 2:1.14.1-2
- Switch to the maint branch
- Related: Jira:RHEL-2112

* Fri Jan 19 2024 Jindrich Novy <jnovy@redhat.com> - 2:1.14.1-1
- update to https://github.com/containers/skopeo/releases/tag/v1.14.1
- Related: RHEL-2112

* Wed Dec 06 2023 Lokesh Mandvekar <lsm5@redhat.com> - 2:1.14.0-1
- bump to v1.14.0
- Related: Jira:RHEL-2112

* Fri Dec 01 2023 Lokesh Mandvekar <lsm5@redhat.com> - 2:1.13.3-3
- Rebuild with golang 1.20.10
- Related: Jira:RHEL-2786

* Fri Dec 01 2023 Lokesh Mandvekar <lsm5@redhat.com> - 2:1.13.3-2
- Rebuild with golang 1.21.3
- Related: Jira:RHEL-2786

* Fri Aug 25 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.13.3-1
- update to https://github.com/containers/skopeo/releases/tag/v1.13.3
- Related: #2176063

* Fri Aug 11 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.13.2-1
- update to https://github.com/containers/skopeo/releases/tag/v1.13.2
- Related: #2176063

* Fri Jul 21 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.13.1-1
- update to https://github.com/containers/skopeo/releases/tag/v1.13.1
- Related: #2176063

* Fri Jul 07 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.13.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.13.0
- Related: #2176063

* Wed Jun 14 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.12.0-3
- rebuild for following CVEs:
CVE-2022-41724 CVE-2022-41725 CVE-2023-24537 CVE-2023-24538 CVE-2023-24534 CVE-2023-24536 CVE-2022-41723 CVE-2023-24539 CVE-2023-24540 CVE-2023-29400
- Resolves: #2179967
- Resolves: #2187323
- Resolves: #2187384
- Resolves: #2203703
- Resolves: #2207523

* Mon Apr 24 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.12.0-2
- remove fakeroot from skopeo-tests
- Related: #2176063

* Wed Apr 19 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.12.0-1
- update to 1.12.0
- Related: #2176063

* Mon Apr 03 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.3-0.1
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.11
  (https://github.com/containers/skopeo/commit/d79588e)
- Related: #2176063

* Sun Mar 26 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.2-0.2
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.11
  (https://github.com/containers/skopeo/commit/8191ef3)
- Related: #2176063

* Tue Feb 21 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.2-0.1
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.11
  (https://github.com/containers/skopeo/commit/3f98753)
- Related: #2124478

* Mon Feb 20 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.1-1
- update to https://github.com/containers/skopeo/releases/tag/v1.11.1
- Related: #2124478

* Fri Jan 27 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.0-1
- update to 1.11.0 release
- Related: #2124478

* Wed Jan 25 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.0-0.4
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/b3b2c73)
- Related: #2124478

* Tue Jan 24 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.0-0.3
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/fe15a36)
- Related: #2124478

* Tue Jan 17 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.0-0.2
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/8e09e64)
- Related: #2124478

* Fri Jan 13 2023 Jindrich Novy <jnovy@redhat.com> - 2:1.11.0-0.1
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/2817510)
- Related: #2124478

* Tue Nov 01 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.10.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.10.0
- Related: #2124478

* Mon Oct 31 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.9.3-1
- update to https://github.com/containers/skopeo/releases/tag/v1.9.3
- Related: #2124478

* Wed Aug 03 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.9.2-1
- update to https://github.com/containers/skopeo/releases/tag/v1.9.2
- Related: #2061316

* Tue Jul 26 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.9.1-1
- update to https://github.com/containers/skopeo/releases/tag/v1.9.1
- Related: #2061316

* Thu Jul 14 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.9.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.9.0
- Related: #2061316

* Fri May 13 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.8.0-4
- Re-enable debuginfo
- Related: #2061316

* Wed May 11 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.8.0-3
- BuildRequires: /usr/bin/go-md2man
- Related: #2061316

* Mon May 09 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.8.0-2
- enable LTO
- Related: #1988128

* Mon May 09 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.8.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.8.0
- Related: #2061316

* Fri Mar 25 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.7.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.7.0
- Related: #2061316

* Mon Mar 14 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.6.1-4
- add tags: classic (Ed Santiago)
- Related: #2061316

* Mon Mar 14 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.6.1-3
- remove BATS from required packages (Ed Santiago)
- Related: #2061316

* Mon Mar 14 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.6.1-2
- be sure to install BATS before gating tests are executed
  (thanks to Ed Santiago)
- Related: #2061316

* Thu Feb 17 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.6.1-1
- update to https://github.com/containers/skopeo/releases/tag/v1.6.1
- Related: #2000051

* Thu Feb 03 2022 Jindrich Novy <jnovy@redhat.com> - 2:1.6.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.6.0
- Related: #2000051

* Mon Nov 29 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.2-1
- update to https://github.com/containers/skopeo/releases/tag/v1.5.2
- Related: #2000051

* Fri Nov 05 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.1-1
- update to https://github.com/containers/skopeo/releases/tag/v1.5.1
- Related: #2000051

* Thu Nov 04 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.1-0.9
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/4acc9f0)
- Related: #2000051

* Wed Oct 27 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.1-0.8
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/c2732cb)
- Related: #2000051

* Mon Oct 25 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.1-0.7
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/01e58f8)
- Related: #2000051

* Thu Oct 21 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.1-0.6
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/8f64c04)
- Related: #2000051

* Mon Oct 18 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.1-0.5
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/8182255)
- Related: #2000051

* Fri Oct 15 2021 Jindrich Novy <jnovy@redhat.com> - 2:1.5.1-0.4
- bump Epoch to preserve upgrade patch from RHEL8
- Related: #2000051

* Wed Oct 13 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.5.1-0.3
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/9c9a9f3)
- Related: #2000051

* Fri Oct 08 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.5.1-0.2
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/116e75f)
- Related: #2000051

* Thu Oct 07 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.5.1-0.1
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/fc81803)
- Related: #2000051

* Wed Oct 06 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.14
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/ff88d3f)
- Related: #2000051

* Mon Oct 04 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.13
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/a95b0cc)
- Related: #2000051

* Fri Oct 01 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.12
- add skopeo tests from Fedora
- Related: #2000051

* Fri Oct 01 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.11
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/53cf287)
- Related: #2000051

* Wed Sep 29 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.10
- add gating.yaml
- Related: #2000051

* Wed Sep 29 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.9
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/86fa758)
- Related: #2000051

* Mon Sep 27 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.8
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/2c2e5b7)
- Related: #2000051

* Thu Sep 23 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.7
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/25d3e7b)
- Related: #2000051

* Wed Sep 22 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.6
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/c5a5199)
- Related: #2000051

* Tue Sep 21 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.5
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/db1e814)
- Related: #2000051

* Fri Sep 17 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.4
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/31b8981)
- Related: #2000051

* Wed Sep 15 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.3
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/177443f)
- Related: #2000051

* Tue Sep 14 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.2
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/30f208e)
- Related: #2000051

* Thu Sep 09 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-0.1
- update to the latest content of https://github.com/containers/skopeo/tree/main
  (https://github.com/containers/skopeo/commit/47b8082)
- Related: #2000051

* Fri Sep 03 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.1-1
- rebuild with containers-common dep fixed
- Related: #2000051

* Tue Aug 10 2021 Mohan Boddu <mboddu@redhat.com> - 1:1.4.0-7
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Fri Aug 06 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-6
- be sure short-name-mode is permissive in RHEL8
- Related: #1970747

* Wed Aug 04 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-5
- don't define short-name-mode in RHEL8
- Related: #1970747

* Wed Aug 04 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-4
- put both RHEL8 and RHEL9 conditional configurations into update.sh
- Related: #1970747

* Wed Aug 04 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-3
- update vendored components
- always require runc on RHEL8 or lesser
- Related: #1970747

* Wed Aug 04 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-2
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.4
  (https://github.com/containers/skopeo/commit/a44da44)
- Related: #1970747

* Tue Aug 03 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-1
- update to 1.4.0 release and switch to the release-1.4 maint branch
- Related: #1970747

* Mon Aug 02 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-0.2
- update vendored components
- ship /etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release only on non-RHEL and
  CentOS distros
- Related: #1970747

* Thu Jul 29 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.4.0-0.1
- switch to the main branch of skopeo
- Related: #1970747

* Tue Jul 27 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-9
- Add support for signed RHEL images, enabled by default
- Related: #1970747

* Mon Jul 26 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-8
- update seccomp.json from Fedora to allow clone3 to pass
- Related: #1970747

* Thu Jul 15 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-7
- update shortnames from Pyxis
- put RHEL9/UBI9 images into overrides
- Related: #1970747

* Wed Jul 07 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-6
- correct name of the option is "short-name-mode" not "short-names-mode"
- Related: #1970747

* Mon Jul 05 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-5
- handle CentOS Stream while updating vendored components
- Related: #1970747

* Mon Jul 05 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-4
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.3
  (https://github.com/containers/skopeo/commit/038f70e)
- Related: #1970747

* Thu Jul 01 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-3
- update registries.conf to be consistent with upstream
- Related: #1970747

* Thu Jul 01 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-2
- consume content from the release-1.3 upstream branch
- Related: #1970747

* Wed Jun 30 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.1-1
- update to https://github.com/containers/skopeo/releases/tag/v1.3.1
- Related: #1970747

* Tue Jun 22 2021 Mohan Boddu <mboddu@redhat.com> - 1:1.3.0-7
- Rebuilt for RHEL 9 BETA for openssl 3.0
  Related: rhbz#1971065

* Tue Jun 15 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.0-6
- set short-names-mode = "enforcing" in registries.conf
- Resolves: #1971752

* Mon Jun 14 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.0-5
- configure for RHEL9
- Related: #1970747

* Mon Jun 14 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.0-4
- add missing containers-mounts.conf.5.md file to git
- don't list/install the same doc twice
- Related: #1970747

* Mon Jun 14 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.3.0-3
- update to new versions of vendored components
- fail is there is an issue in communication with Pyxis API
- understand devel branch in update.sh script, use pkg wrapper
- sync with Pyxis
- use containers-mounts.conf.5.md from containers/common
- Related: #1970747

* Fri Apr 16 2021 Mohan Boddu <mboddu@redhat.com> - 1:1.2.2-4
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Mon Mar 08 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.2-3
- disable LTO again

* Wed Mar 03 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.2-2
- use rhel-shortnames only from trusted registries
- sync with config files from current versions of vendored projects

* Fri Feb 19 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.2-1
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.2
  (https://github.com/containers/skopeo/commit/e72dd9c)

* Fri Feb 19 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-14
- add missing file in sed expression

* Thu Feb 18 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-13
- use %%go_arches again
- Related: #1926597

* Thu Feb 18 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-12
- configure short-name-mode = "enforcing" for RHEL9

* Thu Feb 18 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-11
- disable LTO

* Thu Feb 18 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-10
- rename shortnames.conf to 000-shortnames.conf to assure evaluation order
- Related: #1883490

* Thu Feb 18 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-9
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.2
  (https://github.com/containers/skopeo/commit/3abb778)

* Mon Feb 15 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-8
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.2
  (https://github.com/containers/skopeo/commit/b4210c0)
- Resolves: #1914884

* Sat Feb 06 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-7
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.2
  (https://github.com/containers/skopeo/commit/6c0e35a)

* Wed Feb 03 2021 Jeff Law <law@redhat.com> - 1:1.2.1-6
- Disable LTO

* Tue Feb 02 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-5
- update to the latest content of https://github.com/containers/skopeo/tree/release-1.2
  (https://github.com/containers/skopeo/commit/a05ddb8)

* Sun Jan 31 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-4
- define 8.4.0 branch for podman (v3.0)
- remove redundant source file

* Fri Jan 29 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-3
- convert subscription-manager from weak dep to a hint

* Tue Jan 19 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-2
- fix rhel-shortnames.conf generation (avoid duplicates and records
  with invalid URL)
- Related: #1883490

* Thu Jan 14 2021 Jindrich Novy <jnovy@redhat.com> - 1:1.2.1-1
- ship preconfigured /etc/containers/registries.d/ files with containers-common

* Tue Dec 01 2020 Jindrich Novy <jnovy@redhat.com> - 1:1.2.0-6
- unify vendored branches
- add validation script

* Thu Nov 05 2020 Jindrich Novy <jnovy@redhat.com> - 1:1.2.0-5
- simplify spec file
- use short commit ID in tarball name

* Fri Oct 23 2020 Jindrich Novy <jnovy@redhat.com> - 1:1.2.0-4
- use shortcommit ID in branch tarball name

* Thu Oct 22 2020 Jindrich Novy <jnovy@redhat.com> - 1:1.2.0-3
- update sources and allow to deliver from upstream branch

* Fri Sep 25 2020 Jindrich Novy <jnovy@redhat.com> - 1:1.2.0-2
- fix build of the new skopeo-1.2.0

* Fri Sep 25 2020 Jindrich Novy <jnovy@redhat.com> - 1:1.2.0-1
- update to https://github.com/containers/skopeo/releases/tag/v1.2.0

* Thu Sep 17 2020 Jindrich Novy <jnovy@redhat.com> - 1:1.1.1-4
- sync with rhel8-8.3.0
- propagate proper CFLAGS to CGO_CFLAGS to assure code hardening and optimization
- Related: #1821193

* Wed Jun 19 2019 Eduardo Santiago <santiago@redhat.com> - 1:0.1.37-1
- Resolves: #1720654 - rebase to v0.1.37
- Resolves: #1721247 - enable fips mode
- add emergency debugging patch for figuring out gating-tests problem

* Tue Jun  4 2019 Eduardo Santiago <santiago@redhat.com> - 1:0.1.36-1.git6307635
- built upstream tag v0.1.36, including system tests

* Tue Apr 30 2019 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.32-4.git1715c90
- Fixes @openshift/machine-config-operator#669
- install /etc/containers/oci/hooks.d and /etc/containers/certs.d

* Tue Dec 18 2018 Frantisek Kluknavsky <fkluknav@redhat.com> - 1:0.1.32-3.git1715c90
- rebase

* Mon Dec 17 2018 Frantisek Kluknavsky <fkluknav@redhat.com> - 1:0.1.32-2.git1715c90
- re-enable debuginfo

* Mon Dec 17 2018 Frantisek Kluknavsky <fkluknav@redhat.com> - 1:0.1.31-12.gitb0b750d
- go tools not in scl anymore

* Fri Sep 21 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-11.gitb0b750d
- Resolves: #1615609
- built upstream tag v0.1.31

* Thu Aug 23 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-10.git0144aa8
- Resolves: #1616069 - correct order of registries

* Mon Aug 13 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-9.git0144aa8
- Resolves: #1615609 - rebuild with gobuild tag 'no_openssl'

* Fri Aug 10 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-8.git0144aa8
- Resolves: #1614934 - containers-common soft dep on slirp4netns and
fuse-overlayfs

* Wed Aug 08 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-7.git0144aa8
- build with %%gobuild
- use scl-ized go-toolset as dep
- disable i686 builds temporarily because of go-toolset issues

* Wed Jul 18 2018 dwalsh <dwalsh@redhat.com> - 1:0.1.31-6.git0144aa8
- add statx to seccomp.json to containers-config
- add seccomp.json to containers-config

* Tue Jul 03 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-4.git0144aa8
- Resolves: #1597629 - handle dependency issue for skopeo-containers
- rename skopeo-containers to containers-common as in Fedora

* Mon Jun 25 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-3.git0144aa8
- Resolves: #1583762 - btrfs dep removal needs exclude_graphdriver_btrfs
buildtag

* Wed Jun 13 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-2.git0144aa8
- correct bz in previous changelog

* Wed Jun 13 2018 Lokesh Mandvekar <lsm5@redhat.com> - 1:0.1.31-1.git0144aa8
- Resolves: #1580938 - resolve FTBFS
- Resolves: #1583762 - remove dependency on btrfs-progs-devel
- bump to v0.1.31 (from master)
- built commit ca3bff6
- use go-toolset deps for rhel8

* Tue Apr 03 2018 baude <bbaude@redhat.com> - 0.1.29-5.git7add6fc
- Fix small typo in registries.conf

* Tue Apr 3 2018 dwalsh <dwalsh@redhat.com> - 0.1.29-4.git
- Add policy.json.5

* Mon Apr 2 2018 dwalsh <dwalsh@redhat.com> - 0.1.29-3.git
- Add registries.conf

* Mon Apr 2 2018 dwalsh <dwalsh@redhat.com> - 0.1.29-2.git
- Add registries.conf man page

* Thu Mar 29 2018 dwalsh <dwalsh@redhat.com> - 0.1.29-1.git
- bump to 0.1.29-1
- Updated containers/image
    docker-archive generates docker legacy compatible images
    Do not create $DiffID subdirectories for layers with no configs
    Ensure the layer IDs in legacy docker/tarfile metadata are unique
    docker-archive: repeated layers are symlinked in the tar file
    sysregistries: remove all trailing slashes
    Improve docker/* error messages
    Fix failure to make auth directory
    Create a new slice in Schema1.UpdateLayerInfos
    Drop unused storageImageDestination.{image,systemContext}
    Load a *storage.Image only once in storageImageSource
    Support gzip for docker-archive files
    Remove .tar extension from blob and config file names
    ostree, src: support copy of compressed layers
    ostree: re-pull layer if it misses uncompressed_digest|uncompressed_size
    image: fix docker schema v1 -> OCI conversion
    Add /etc/containers/certs.d as default certs directory

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.28-2.git0270e56
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Feb 2 2018 dwalsh <dwalsh@redhat.com> - 0.1.28-1.git
- Vendor in fixed libraries in containers/image and containers/storage

* Tue Nov 21 2017 dwalsh <dwalsh@redhat.com> - 0.1.27-1.git
- Fix Conflicts to Obsoletes
- Add better docs to man pages.
- Use credentials from authfile for skopeo commands
- Support storage="" in /etc/containers/storage.conf
- Add global --override-arch and --override-os options

* Wed Nov 15 2017 dwalsh <dwalsh@redhat.com> - 0.1.25-2.git2e8377a7
-  Add manifest type conversion to skopeo copy
-  User can select from 3 manifest types: oci, v2s1, or v2s2
-   e.g skopeo copy --format v2s1 --compress-blobs docker-archive:alp.tar dir:my-directory

* Wed Nov 8 2017 dwalsh <dwalsh@redhat.com> - 0.1.25-2.git7fd6f66b
- Force storage.conf to default to overlay

* Wed Nov 8 2017 dwalsh <dwalsh@redhat.com> - 0.1.25-1.git7fd6f66b
-   Fix CVE in tar-split
-   copy: add shared blob directory support for OCI sources/destinations
-   Aligning Docker version between containers/image and skopeo
-   Update image-tools, and remove the duplicate Sirupsen/logrus vendor
-   makefile: use -buildmode=pie
  
* Tue Nov 7 2017 dwalsh <dwalsh@redhat.com> - 0.1.24-8.git28d4e08a
- Add /usr/share/containers/mounts.conf

* Sun Oct 22 2017 dwalsh <dwalsh@redhat.com> - 0.1.24-7.git28d4e08a
- Bug fixes
- Update to release

* Tue Oct 17 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.24-6.dev.git28d4e08
- skopeo-containers conflicts with docker-rhsubscription <= 2:1.13.1-31

* Tue Oct 17 2017 dwalsh <dwalsh@redhat.com> - 0.1.24-5.dev.git28d4e08
- Add rhel subscription secrets data to skopeo-containers

* Thu Oct 12 2017 dwalsh <dwalsh@redhat.com> - 0.1.24-4.dev.git28d4e08
- Update container/storage.conf and containers-storage.conf man page
- Default override to true so it is consistent with RHEL.

* Tue Oct 10 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.24-3.dev.git28d4e08
- built commit 28d4e08

* Mon Sep 18 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.24-2.dev.git875dd2e
- built commit 875dd2e
- Resolves: gh#416

* Tue Sep 12 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.24-1.dev.gita41cd0
- bump to 0.1.24-dev
- correct a prior bogus date
- fix macro in comment warning

* Mon Aug 21 2017 dwalsh <dwalsh@redhat.com> - 0.1.23-6.dev.git1bbd87
- Change name of storage.conf.5 man page to containers-storage.conf.5, since
it conflicts with inn package
- Also remove default to "overalay" in the configuration, since we should
- allow containers storage to pick the best default for the platform.

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.23-5.git1bbd87f
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Sun Jul 30 2017 Florian Weimer <fweimer@redhat.com> - 0.1.23-4.git1bbd87f
- Rebuild with binutils fix for ppc64le (#1475636)

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.23-3.git1bbd87f
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Tue Jul 25 2017 dwalsh <dwalsh@redhat.com> - 0.1.23-2.dev.git1bbd87
- Fix storage.conf man page to be storage.conf.5.gz so that it works.

* Fri Jul 21 2017 dwalsh <dwalsh@redhat.com> - 0.1.23-1.dev.git1bbd87
- Support for OCI V1.0 Images
- Update to image-spec v1.0.0 and revendor
- Fixes for authentication

* Sat Jul 01 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.22-2.dev.git5d24b67
- Epoch: 1 for CentOS as CentOS Extras' build already has epoch set to 1

* Wed Jun 21 2017 dwalsh <dwalsh@redhat.com> - 0.1.22-1.dev.git5d24b67
-  Give more useful help when explaining usage
-  Also specify container-storage as a valid transport
-  Remove docker reference wherever possible
-  vendor in ostree fixes

* Thu Jun 15 2017 dwalsh <dwalsh@redhat.com> - 0.1.21-1.dev.git0b73154
- Add support for storage.conf and storage-config.5.md from github container storage package
- Bump to the latest version of skopeo
- vendor.conf: add ostree-go
- it is used by containers/image for pulling images to the OSTree storage.
- fail early when image os does not match host os
- Improve documentation on what to do with containers/image failures in test-skopeo
-   We now have the docker-archive: transport
-   Integration tests with built registries also exist
- Support /etc/docker/certs.d
- update image-spec to v1.0.0-rc6

* Tue May 23 2017 bbaude <bbaude@redhat.com> - 0.1.20-1.dev.git0224d8c
- BZ #1380078 - New release

* Tue Apr 25 2017 bbaude <bbaude@redhat.com> - 0.1.19-2.dev.git0224d8c
- No golang support for ppc64.  Adding exclude arch. BZ #1445490

* Tue Feb 28 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.19-1.dev.git0224d8c
- bump to v0.1.19-dev
- built commit 0224d8c

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.17-3.dev.git2b3af4a
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Sat Dec 10 2016 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.1.17-2.dev.git2b3af4a
- Rebuild for gpgme 1.18

* Tue Dec 06 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.17-1.dev.git2b3af4a
- bump to 0.1.17-dev

* Fri Nov 04 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.14-6.git550a480
- Fix BZ#1391932

* Tue Oct 18 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.14-5.git550a480
- Conflicts with atomic in skopeo-containers

* Wed Oct 12 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.14-4.git550a480
- built skopeo-containers

* Wed Sep 21 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.14-3.gitd830391
- built mtrmac/integrate-all-the-things commit d830391

* Thu Sep 08 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.14-2.git362bfc5
- built commit 362bfc5

* Thu Aug 11 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.14-1.gitffe92ed
- build origin/master commit ffe92ed

* Thu Jul 21 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.13-6
- https://fedoraproject.org/wiki/Changes/golang1.7

* Tue Jun 21 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 0.1.13-5
- include go-srpm-macros and compiler(go-compiler) in fedora conditionals
- define %%gobuild if not already
- add patch to build with older version of golang

* Thu Jun 02 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.13-4
- update to v0.1.12

* Tue May 31 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.12-3
- fix go build source path

* Fri May 27 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.12-2
- update to v0.1.12

* Tue Mar 08 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.11-1
- update to v0.1.11

* Tue Mar 08 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.10-1
- update to v0.1.10
- change runcom -> projectatomic

* Mon Feb 29 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.9-1
- update to v0.1.9

* Mon Feb 29 2016 Antonio Murdaca <runcom@fedoraproject.org> - 0.1.8-1
- update to v0.1.8

* Mon Feb 22 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.4-2
- https://fedoraproject.org/wiki/Changes/golang1.6

* Fri Jan 29 2016 Antonio Murdaca <runcom@redhat.com> - 0.1.4
- First package for Fedora

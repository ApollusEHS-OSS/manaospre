# statically linked version for firmware updater

SUMMARY = "Ext2 Filesystem Utilities"
DESCRIPTION = "The Ext2 Filesystem Utilities (e2fsprogs) contain all of \
the standard utilities for creating, fixing, configuring , and debugging \
ext2 filesystems."

HOMEPAGE = "http://e2fsprogs.sourceforge.net/"

inherit autotools gettext texinfo pkgconfig multilib_header update-alternatives ptest

LICENSE = "GPLv2 & LGPLv2 & BSD & MIT"

SRC_URI = "git://git.kernel.org/pub/scm/fs/ext2/e2fsprogs.git"
SRCREV = "984ff8d6a0a1d5dc300505f67b38ed5047d51dac"
S = "${WORKDIR}/git"

LIC_FILES_CHKSUM = "file://NOTICE;md5=d50be0580c0b0a7fbc7a4830bbe6c12b"

EXTRA_OECONF_append=" LDFLAGS=--static"

do_install () {
    install -m 0755 -d ${D}${base_sbindir}
    install -m 0755 ${B}/e2fsck/e2fsck ${D}${base_sbindir}
}

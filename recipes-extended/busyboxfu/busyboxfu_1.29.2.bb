# Firmware Updater version of busybox (w/static linking)

SUMMARY = "Tiny versions of many common UNIX utilities in a single small executable"
DESCRIPTION = "BusyBox combines tiny versions of many common UNIX utilities into a single small executable. It provides minimalist replacements for most of the utilities you usually find in GNU fileutils, shellutils, etc. The utilities in BusyBox generally have fewer options than their full-featured GNU cousins; however, the options that are included provide the expected functionality and behave very much like their GNU counterparts. BusyBox provides a fairly complete POSIX environment for any small or embedded system."
HOMEPAGE = "http://www.busybox.net"
BUGTRACKER = "https://bugs.busybox.net/"

SECTION = "base"

inherit autotools

LICENSE = "GPLv2 & bzip2"
LIC_FILES_CHKSUM = "file://LICENSE;md5=de10de48642ab74318e893a61105afbb"


SRC_URI = " \
    http://www.busybox.net/downloads/busybox-${PV}.tar.bz2;name=tarball \
    file://defconfig \
    "

SRC_URI[tarball.md5sum] = "46617af37a39579711d8b36f189cdf1e"
SRC_URI[tarball.sha256sum] = "67d2fa6e147a45875fe972de62d907ef866fe784c495c363bf34756c444a5d61"

# Work around the busyboxfu package name (vs. busybox)
REALPN = "busybox"
S = "${WORKDIR}/${REALPN}-${PV}"
B = "${S}"

do_configure() {
    cp ../defconfig .config
    make oldconfig
}

do_compile() {
    make ${PARALLEL_MAKE}
}

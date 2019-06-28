SUMMARY = "general-purpose software audio FSK modem"
DESCRIPTION = "Minimodem is a command-line program which decodes \
(or generates) audio \
modem tones at any specified baud rate, using various framing protocols. \
It acts a general-purpose software FSK modem, and includes support for \
various standard FSK protocols such as Bell103, Bell202, RTTY, TTY/TDD, \
NOAA SAME, and Caller-ID."

HOMEPAGE = "http://www.whence.com/minimodem/"

SECTION = "console/network"
DEPENDS += " fftw libsndfile1"

inherit autotools pkgconfig

LICENSE = "GPLv3"
LIC_FILES_CHKSUM = "file://COPYING;md5=f5d8ec1ef3bbed632ec2600200c5aa94"
FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}-${PV}:"

# minimodem 0.24-1
SRC_URI = "git://github.com/kamalmostafa/minimodem.git;branch=master"
#SRC_URI[md5sum] = "7430dc7d9edd7aa6e6317cc8e631565b"
SRCREV = "17e17b784ea83e97e84dacb813ccec25072dbd1d"

S = "${WORKDIR}/git"

EXTRA_OECONF_append="--without-alsa --without-pulseaudio"

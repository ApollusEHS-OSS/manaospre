SUMMARY = "MagicModem init extras"
DESCRIPTION = "Extra items init system for the MagicModem"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COREBASE}/meta/COPYING.MIT;md5=3da9cfbcb788c80a0384361b4de20420"

#TODO: add python
DEPENDS += "busybox minimodem iproute2 iptables"
RDEPENDS_${PN} += " iproute2-tc"

SRC_URI = "file://rc.magicmodem file://rcd-magicmodem file://screenrc"

S = "${WORKDIR}"

inherit update-rc.d

# TODO: split out the components of the startup to proper init pieces
# TODO: remove rcd-magicmodem
INITSCRIPT_PACKAGES = "${PN}"
INITSCRIPT_NAME = "rcd-magicmodem"
INITSCRIPT_PARAMS_${PN} = "defaults 99"

do_configure() {
	:
}

do_compile() {
	:
}

do_install_append() {
    install -d ${D}${sysconfdir}
    install -m 0755 ${S}/screenrc ${D}${sysconfdir}

    install -d ${D}${sysconfdir}/init.d
    install -m 0755 ${S}/rc.magicmodem ${D}${sysconfdir}/init.d
    # TODO: remove rcd-magicmodem
    install -m 0755 ${S}/rcd-magicmodem ${D}${sysconfdir}/init.d
}

#FILES_${PN} = "${sysconfdir}/rc.magicmodem ${sysconfdir}/screenrc"

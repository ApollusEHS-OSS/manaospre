# TODO: add the patch, but may need to bump hostapd
#FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}:"

# TODO: figure out why hostapd.conf isn't getting overwritten
FILESEXTRAPATHS_prepend := "${THISDIR}/files:"

do_install_append() {
    cat > ${D}${sysconfdir}/init.d/hostapd << EOF
#!/bin/sh
#
# "disabling init for hostapd"
exit 0
EOF
}

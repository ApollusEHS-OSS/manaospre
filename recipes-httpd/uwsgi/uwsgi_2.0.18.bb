SUMMARY = "uWSGI provides WSGI web server support"
DESCRIPTION = "The uWSGI project aims at developing a full stack for \
building hosting services."

HOMEPAGE = "https://uwsgi-docs.readthedocs.io/en/latest/"

SECTION = "net"
DEPENDS += "expat pcre python zlib"

inherit pythonnative python3native setuptools3

LICENSE = "GPLv2"
LIC_FILES_CHKSUM = "file://LICENSE;md5=33ab1ce13e2312dddfad07f97f66321f"
FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}-${PV}:"

# uwsgi 2.0.18
SRC_URI = "git://github.com/unbit/uwsgi.git;branch=uwsgi-2.0"
SRC_URI[md5sum] = "7430dc7d9edd7aa6e6317cc8e631565b"
SRCREV = "d1338dfefe3d9a2de466a9a695cb61fdd055a295"

S = "${WORKDIR}/git"


do_configure() {
    sed -i -e "s|'pcre-config --libs'|'pkg-config --libs libpcre'|g" \
        -e 's|"pcre-config --cflags"|"pkg-config --cflags libpcre"|g' \
        ${S}/uwsgiconfig.py
}

do_compile() {
    # build a stripped down core uwsgi
    python2 uwsgiconfig.py --build core

    # add functionality through the plugins
    python3.5 uwsgiconfig.py --plugin plugins/corerouter core
    python3.5 uwsgiconfig.py --plugin plugins/http core
    python3.5 uwsgiconfig.py --plugin plugins/python core python35
    python3.5 uwsgiconfig.py --plugin plugins/syslog core
}

pluginsdir = "${libdir}/uwsgi/plugins"
do_install() {
    install -m 0755 -d ${D}${bindir}
    install -m 0755 ${S}/uwsgi ${D}${bindir}

    install -m 0755 -d ${D}${pluginsdir}
    install -m 0644 ${S}/corerouter_plugin.so ${D}${pluginsdir}
    install -m 0644 ${S}/http_plugin.so ${D}${pluginsdir}
    install -m 0644 ${S}/python35_plugin.so ${D}${pluginsdir}
    install -m 0644 ${S}/syslog_plugin.so ${D}${pluginsdir}
}

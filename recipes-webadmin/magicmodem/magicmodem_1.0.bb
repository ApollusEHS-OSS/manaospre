SUMMARY = "magicmodem provides web admin for global traffic shaping"

HOMEPAGE = "http://blogofsomeguy.com/"

SECTION = "net"
DEPENDS += "python"

# TODO: remove python-jinja2 by updating hostapconfgenerator to py3
RDEPENDS_${PN} += "python3-flask python-pysqlite python-jinja2"

inherit pythonnative python3native

LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=8cb0e7532cec2181a87da379f8c6d75a"
FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}-${PV}:"

SRC_URI = "file://LICENSE \
    file://LCDd.conf \
    file://webui/wiphyutils.py \
    file://webui/fonts/fontawesome-webfont.woff \
    file://webui/fonts/fontawesome-webfont.eot \
    file://webui/fonts/fontawesome-webfont.woff2 \
    file://webui/fonts/fontawesome-webfont.ttf \
    file://webui/fonts/fontawesome-webfont.svg \
    file://webui/fonts/FontAwesome.otf \
    file://webui/i/flags32.png \
    file://webui/i/net.png \
    file://webui/i/flags32a.css \
    file://webui/i/mmlogo.png \
    file://webui/i/font-awesome.css \
    file://webui/i/Chart.min.js \
    file://webui/i/base.css \
    file://webui/i/search.js \
    file://webui/search.html \
    file://webui/main.py \
    file://updaterouting.py \
    file://zeroshaping.sh \
    file://calibrate.py \
    file://display.py \
    file://hostapconfgenerator.py \
    file://lcdproc/LICENSE \
    file://lcdproc/server.py \
    file://lcdproc/widgets.py \
    file://lcdproc/__init__.py \
    file://lcdproc/screen.py \
    file://shaping.db"


#SRC_URI[md5sum] = "7430dc7d9edd7aa6e6317cc8e631565b"

S = "${WORKDIR}"


do_configure() {
    :
}

do_compile() {
    :
}

appdir = "/apps/magicmodem"
webappdir = "${appdir}/webui"

do_install() {
    install -m 0755 -d ${D}${appdir}
    install -m 0600 ${S}/LICENSE ${D}${appdir}
    install -m 0600 ${S}/LCDd.conf ${D}${appdir}
    install -m 0600 ${S}/updaterouting.py ${D}${appdir}
    install -m 0755 ${S}/zeroshaping.sh ${D}${appdir}
    install -m 0600 ${S}/calibrate.py ${D}${appdir}
    install -m 0600 ${S}/display.py ${D}${appdir}
    install -m 0600 ${S}/hostapconfgenerator.py ${D}${appdir}

    install -m 0755 -d ${D}${webappdir}
    install -m 0600 ${S}/webui/wiphyutils.py ${D}${webappdir}
    install -m 0600 ${S}/webui/search.html ${D}${webappdir}
    install -m 0600 ${S}/webui/main.py ${D}${webappdir}

    install -m 0755 -d ${D}${webappdir}/fonts
    install -m 0600 ${S}/webui/fonts/fontawesome-webfont.woff ${D}${webappdir}/fonts
    install -m 0600 ${S}/webui/fonts/fontawesome-webfont.eot ${D}${webappdir}/fonts
    install -m 0600 ${S}/webui/fonts/fontawesome-webfont.woff2 ${D}${webappdir}/fonts
    install -m 0600 ${S}/webui/fonts/fontawesome-webfont.ttf ${D}${webappdir}/fonts
    install -m 0600 ${S}/webui/fonts/fontawesome-webfont.svg ${D}${webappdir}/fonts
    install -m 0600 ${S}/webui/fonts/FontAwesome.otf ${D}${webappdir}/fonts

    install -m 0755 -d ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/flags32.png ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/net.png ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/flags32a.css ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/mmlogo.png ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/font-awesome.css ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/Chart.min.js ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/base.css ${D}${webappdir}/i
    install -m 0600 ${S}/webui/i/search.js ${D}${webappdir}/i

    install -m 0755 -d ${D}${appdir}/lcdproc
    install -m 0600 ${S}/lcdproc/LICENSE ${D}${appdir}/lcdproc
    install -m 0600 ${S}/lcdproc/server.py ${D}${appdir}/lcdproc
    install -m 0600 ${S}/lcdproc/widgets.py ${D}${appdir}/lcdproc
    install -m 0600 ${S}/lcdproc/__init__.py ${D}${appdir}/lcdproc
    install -m 0600 ${S}/lcdproc/screen.py ${D}${appdir}/lcdproc

    # TODO: remove this, it should be a separate installable
    install -m 0755 -d ${D}/apps/magicmodem-data
    install -m 0600 ${S}/shaping.db ${D}/apps/magicmodem-data
}

FILES_${PN} = "${appdir}/LICENSE ${appdir}/LCDd.conf ${webappdir}/wiphyutils.py ${webappdir}/fonts/fontawesome-webfont.woff ${webappdir}/fonts/fontawesome-webfont.eot ${webappdir}/fonts/fontawesome-webfont.woff2 ${webappdir}/fonts/fontawesome-webfont.ttf ${webappdir}/fonts/fontawesome-webfont.svg ${webappdir}/fonts/FontAwesome.otf ${webappdir}/i/flags32.png ${webappdir}/i/net.png ${webappdir}/i/flags32a.css ${webappdir}/i/mmlogo.png ${webappdir}/i/font-awesome.css ${webappdir}/i/Chart.min.js ${webappdir}/i/base.css ${webappdir}/i/search.js ${webappdir}/search.html ${webappdir}/main.py ${appdir}/updaterouting.py ${appdir}/zeroshaping.sh ${appdir}/calibrate.py ${appdir}/display.py ${appdir}/hostapconfgenerator.py ${appdir}/lcdproc/LICENSE ${appdir}/lcdproc/server.py ${appdir}/lcdproc/widgets.py ${appdir}/lcdproc/__init__.py ${appdir}/lcdproc/screen.py /apps/magicmodem-data/shaping.db"

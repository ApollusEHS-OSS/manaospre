# TODO: Figure out why this doesn't work with the git repo
#  (it seems to only look for the files there or accept a patch)
#FILESEXTRAPATHS_prepend := "${THISDIR}/files:"
#SRC_URI += " file://LCDd.conf-override"

PACKAGECONFIG_append_pn-${PN} = " usb ftdi"
LCD_DRIVERS_append_pn-${PN} = " CFontzPacket"
RDEPENDS_${PN} += " lcdd-driver-cfontzpacket"

do_install_append () {
    # TODO: figure out why this doesn't work
    #install -D -m 0644 ${S}/LCDd.conf-override \
    #    ${D}${sysconfdir}/LCDd.conf.2

    # WARNING!  MEGA HACK UP NEXT!!!!!
    # but alas, there's no time left to Do The Right Thing(tm)
    cat > ${D}${sysconfdir}/LCDd.conf <<EOF2
[server]
DriverPath=/usr/lib/lcdproc/
Driver=CFontzPacket
Bind=127.0.0.1
Port=13666
#ReportLevel=3
ReportToSyslog=yes
User=nobody
#Foreground=yes

Hello="Magic Modem"
Hello="Online!"
GoodBye="Netflix says:"
GoodBye="...ship it!"

WaitTime=5
ServerScreen=blank
#Backlight=open
#Heartbeat=open
#TitleSpeed=10

# The "...Key=" lines define what the server does with keypresses that
# don't go to any client. The ToggleRotateKey stops rotation of screens, while
# the PrevScreenKey and NextScreenKey go back / forward one screen (even if
# rotation is disabled.
# Assign the key string returned by the driver to the ...Key setting. These
# are the defaults:
ToggleRotateKey=Enter
PrevScreenKey=Left
NextScreenKey=Right
#ScrollUpKey=Up
#ScrollDownKey=Down


## The menu section. The menu is an internal LCDproc client. ##
[menu]
# You can configure what keys the menu should use. Note that the MenuKey
# will be reserved exclusively, the others work in shared mode.

# Up to six keys are supported. The MenuKey (to enter and exit the menu), the
# EnterKey (to select values) and at least one movement keys are required.
# These are the default key assignments:
#MenuKey=Escape
EnterKey=Enter
UpKey=Up
DownKey=Down
#LeftKey=Left
#RightKey=Right


### Driver sections are below this line, in alphabetical order  ###


## CrystalFontz packet driver (for CFA533, CFA631, CFA633 & CFA635) ##
[CFontzPacket]
Model=635
Device=/dev/ttyACM0
Contrast=560
# Set the initial brightness [default: 1000; legal: 0 - 1000]
Brightness=1000
OffBrightness=50
Reboot=yes
USB=yes

# EOF
EOF2
}

# [manaos](http://www.manaos.org) preview release
Welcome to the meta-manaos yocto layer, powering the magicmodem!

This is currently a prerelease alpha.  While this code
has been used on a number of installations, it should be considered very
early stage and listly tested.

The datapack is also in a very early stage and hasn't been extensively
validated.  The next steps are to sort out installations (primarily on
the PCEngines APU2), add ARM target support, and to cut down on the lengthy
list of TODOs.

Use at your own risk, and check out the license details.

## Build
Building is roughly:
```
# arrange a basic yocto thud build, assuming the directory is poky:
mkdir mm && cd mm
git clone -b thud git://git.yoctoproject.org/poky.git
cd poky
git clone THISREPO meta-manaos
echo 'TEMPLATECONF=${TEMPLATECONF:-meta-manaos/conf}' > .templateconf

# Yocto help: https://www.yoctoproject.org/docs/2.6/brief-yoctoprojectqs/brief-yoctoprojectqs.html
# tools you probably need if you don't have them already, ubuntu example:
sudo apt-get install -y gawk wget git-core diffstat unzip texinfo gcc-multilib \
     build-essential chrpath socat cpio python python3 python3-pip python3-pexpect \
     xz-utils debianutils iputils-ping libsdl1.2-dev xterm

git checkout tags/yocto-2.6 -b mm
git clone https://github.com/openembedded/meta-openembedded.git
cd meta-openembedded && git checkout thud && cd ..

source oe-init-build-env
# customize to taste, then
bitbake core-image-minimal

# after a successful build:
../meta-manaos/scripts/buildfirmwareupdater.py
../meta-manaos/scripts/glueimg.py
```

## Sharp Edges
Here's a few gotchas:
* The resulting image will have no root password.  Set one for non-dev use!
* use `glueimg.py` to make a complete image (see below)
* AP settings are not currently saved (coming!).  Radio settings are
    currently defaulted for use in the US.  Respect the RF laws and
    requirements of your country of operation before using this image with
    a wireless adapter!
* The simulation is currently only intended for a single user at a time.
    Attaching multiple users to the same MM will result in an unrealistic
    scenario (dividing the bandwidth), if you're concerned with accuracy.
* The ficticious country of Quamom (QM) is used for High, Medium, and Low
    profiles.  These are based on real ISP data which was arbitrarily
    selected and will be subject to change when better criteria for
    determining this is available.

## Gluing together a firmware
`glueimg.py` is a stand in until there's time to integrate WIC.  Barring
any errors, it usually drops the resulting image in /tmp/manaos.img, along
with some hints on how to run it in VirtualBox or to dd a USB stick for
booting hardware.

## Basic Use
After writing an image out to a USB stick, it should boot on an APU2 or on
VirtualBox (check the `glueimg.py` hints, which are still very sparse). To
work around some boot issues, follow these steps:

1. Plug the WAN (left) port to your internet connection.
2. Plug your browser device to either of the bonded LAN ports (middle/right).
3. Turn the device on.  Boot and calibration take about a minute.
4. After the WAN interface comes up, dhcp should work on the LAN ports.
  Check with `ping 192.168.20.1` at a shell.
5. Navigate to http://192.168.20.1:9090/ and select an ISP through the search
  blank.  Type either an ASN name, an ASN number, or an ISO3166 2 letter
  country code.
6. Selecting the plus icon will add it to your favorites, while selecting the
  tachometer icon will instantly shape your connection the median UTC midnight
  experience of that ISP (practical teleportation).  Time traveling is
  planned for later.

[Instructions for VirtualBox builds are here](http://www.manaos.org/article).

NB - All routes are not currently shaped, mainly access to AWS and OpenConnect.
There isn't an interface to adjust this yet.

## License
See COPYING.MIT.  Yocto software and included modules are under their own
respective licenses (see the bitbake license src files).

----
In case you were wondering, it _is_ actually a modem.  A message is
modulated at 1200bps and then demodulated during boot time.  Thank you
minimodem for the Bell202 implementation!

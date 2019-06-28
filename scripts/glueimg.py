#!/usr/bin/python3

# Beware, perl-like hackery ensues
# TODO: rewrite this with wic after moving to syslinux (grub / non-efi issues)


# TODO: this doesn't clean up if it errors mid way through
#       (loopbacks / mounts will remain open)

import sys
import os
import shutil
from math import ceil

# get wic.misc.get_bitbake_var for build variables
BB_PATHS = {}
BB_PATHS["basepath"] = os.path.join(os.path.dirname(__file__), "..", "..")
BB_PATHS["poky_scripts"] = os.path.join(BB_PATHS["basepath"], "scripts", "lib")
sys.path.append(BB_PATHS["poky_scripts"])
from wic.misc import get_bitbake_var

# TODO: don't package this in /tmp, use a drive with space
FIRMWARE_FILE_FULL_PATH = "/tmp/manaos.img"
# TODO: handle if this is too small :(
FIRMWARE_SIZE_MB = 384
FIRMWARE_DISKUSE_PERCENTAGE = 0.98
FIRMWARE_DISK_ALLOCATION = ceil(FIRMWARE_SIZE_MB / FIRMWARE_DISKUSE_PERCENTAGE)

# TODO: use the TOOLS vars in commands
TOOLS = {
    "parted": "/sbin/parted",
    "dd": "/bin/dd",
    "fsck.ext2": "/sbin/fsck.ext2",
    "resize2fs": "/sbin/resize2fs",
    "mount": "/bin/mount",
    "umount": "/bin/umount",
    "losetup": "/sbin/losetup",
    "grub-install": "/usr/sbin/grub-install",
}

# check if a file is there, provide a hint if it isn't
NEEDED_FILES = [
    # TODO: remove the host grub dep, use the yocto tool
    ["/usr/lib/grub/i386-pc/modinfo.sh", "sudo apt install grub-pc-bin"],
]


def sanity_check(firmware_full_path):
    try:
        os.unlink(firmware_full_path)
    except FileNotFoundError:
        pass

    path = os.path.split(firmware_full_path)[0]
    # TODO: figure out why this isn't working
    if shutil.disk_usage(path).free <= (FIRMWARE_SIZE_MB * 1024 * 1024):
        print("Not enough free space to create the firmware")
        exit(2)

    # TODO: check FIRMWARE_SIZE_MB > needed fs size from build

    # check for the needed tools:
    for tool, tool_full_path in TOOLS.items():
        if os.path.isfile(tool_full_path) == False:
            print("tool [%s] wasn't found at [%s], exiting" % (
                tool, tool_full_path))
            exit(3)

    # check for NEEDED_FILES
    for (file_full_path, missing_hint) in NEEDED_FILES:
        if os.path.isfile(file_full_path) == False:
            print("required file [%s] wasn't found. Perhaps [%s]" % (file_full_path, missing_hint))
            exit(3)


def system_should_succeed(cmd):
    print("system_should_succeed:\n  %s" % cmd)
    rc = os.system(cmd)
    if rc != 0:
        print("system_should_succeed exited with return code [%d], exiting" % rc)
        exit(4)


# TODO: unsafe, should clear the pipe
def pipe_should_succeed(cmd):
    print("pipe_should_succeed:\n  %s" % cmd)

    buf = ""
    p = os.popen(cmd)
    while True:
        line = p.readline()
        buf += line

        if line == "":
            break

    rc = p.close()
    if rc is not None:
        print("pipe_should_succeed exited with return code [%d], aborting" % rc)
        exit(5)

    return buf


def do_gluing(firmware_full_path, yocto_rootfs_full_path):
    print("do_gluing: invoked")
    disk_use_as_percent_int = ceil(FIRMWARE_DISKUSE_PERCENTAGE * 100.0)
    cmd = [
        TOOLS["dd"] + " if=/dev/zero of=%s bs=1M count=1 seek=%d",
        TOOLS["parted"] + " -s %s -- mklabel msdos mkpart primary fat32 1 %d%% toggle 1 boot",
        TOOLS["losetup"] + " --show -Pf %s",
        TOOLS["dd"] + " if=%s of=%sp1 bs=4M",
        TOOLS["fsck.ext2"] + " -p %sp1",
        TOOLS["resize2fs"] + " %sp1",
        TOOLS["losetup"] + " -d %s",
    ]

    # create an empty fs image to work with:
    system_should_succeed(cmd[0] % (firmware_full_path, FIRMWARE_DISK_ALLOCATION))

    # partition the empty fs image:
    system_should_succeed(cmd[1] % (firmware_full_path, disk_use_as_percent_int))

    # TODO: check there isn't already a loopback device for this file open
    #   (such as from a previous crash)
    # get a loopback mount device:
    loopback_device = pipe_should_succeed(cmd[2] % firmware_full_path)
    loopback_device = loopback_device.strip()

    # mix in the yocto_rootfs:
    system_should_succeed(cmd[3] % (yocto_rootfs_full_path, loopback_device))

    #Disabled these check / resize due to some version oddities on xenial
    # check / fix the fs
    #system_should_succeed(cmd[4] % loopback_device)

    # resize the fs to the full image size
    #system_should_succeed(cmd[5] % loopback_device)

    # close the loopback device
    system_should_succeed(cmd[6] % loopback_device)
    print("do_gluing: done")


def do_grub_and_kernel_install(firmware_full_path, kernel_full_path):
    cmd = [
        TOOLS["losetup"] + " --show -Pf %s",
        TOOLS["mount"] + " %sp1 %s/",
        TOOLS["grub-install"] + " --target i386-pc --boot-directory=%s/boot --modules=part_msdos %s",
        TOOLS["umount"] + " %s/",
        TOOLS["losetup"] + " -d %s",
    ]

    # make a mountpoint
    firmwarepath = os.path.split(firmware_full_path)[0]
    mount_point = os.path.join(firmwarepath, "mtpt")
    os.makedirs(mount_point, exist_ok=True)

    # get a loopback mount device:
    loopback_device = pipe_should_succeed(cmd[0] % firmware_full_path)
    loopback_device = loopback_device.strip()

    # mount the device
    system_should_succeed(cmd[1] % (loopback_device, mount_point))

    # install grub:
    system_should_succeed(cmd[2] % (mount_point, loopback_device))

    # write out the grub.cfg
    # TODO: don't inline the grubconfig, well, just remove grub
    with open(os.path.join(mount_point, "boot", "grub", "grub.cfg"), "w") as f:
        grub_config = """set default="0"
set timeout="2"

menuentry "ManaOS" {
    echo "Loading..."
    set gfxpayload=vga=off
    linux /boot/bzImage root=/dev/sda1 rootwait console=ttyS0,115200n8
}

menuentry "ManaOS (VGA)" {
    echo "Loading..."
    insmod vga
    linux /boot/bzImage root=/dev/sda1 rootwait
}"""
        f.write(grub_config)

    # copy the kernel into the fs
    shutil.copy(kernel_full_path, os.path.join(mount_point, "boot"),
        follow_symlinks=True)

    # unmount the device
    system_should_succeed(cmd[3] % mount_point)

    # close the loopback device
    system_should_succeed(cmd[4] % loopback_device)
    print("do_gluing: done")


def print_hints(firmware_full_path):
    filename = os.path.split(firmware_full_path)[1]
    # TODO: repair qemu support
    #qemu-system-x86_64 -snapshot -hda %s -boot c -serial mon:vc -serial null
    hints = """\n\n%s is ready, can test/write with:
    VBoxManage convertfromraw --format vdi %s ~/manaos.vdi
    sudo dd if=%s of=/dev/sdX bs=4M status=progress
    """ % (firmware_full_path,
        firmware_full_path, firmware_full_path)
    print(hints)


def do_glue_image(firmware_full_path, yocto_full_path, kernel_full_path):
    if os.geteuid() != 0:
        print("This script requires root privileges for" \
                " loopback, mounting, and fsck, exiting")
        exit(1)

    sanity_check(firmware_full_path)

    do_gluing(firmware_full_path, yocto_full_path)
    do_grub_and_kernel_install(firmware_full_path, kernel_full_path)

    print_hints(firmware_full_path)


if __name__ == "__main__":
    # TODO: find a yocto way to import the vars as sudo instead

    if len(sys.argv) == 1:
        # first execution in bitbake env, get paths
        deploy_dir_image = get_bitbake_var("DEPLOY_DIR_IMAGE")
        yocto_full_path = os.path.join(
            deploy_dir_image, "core-image-minimal-qemux86-64.ext4")
        kernel_full_path = os.path.join(
            deploy_dir_image, "bzImage")
        os.execvp("sudo", ["python3", __file__, yocto_full_path, kernel_full_path])
    elif len(sys.argv) == 3:
        # second execution in sudo context
        _, yocto_full_path, kernel_full_path = sys.argv
        do_glue_image(FIRMWARE_FILE_FULL_PATH, yocto_full_path, kernel_full_path)
    else:
        print("Usage:\n  %s\nor\n  %s yocto_full_path kernel_full_path" % (
            __file__, __file__))

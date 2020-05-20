#!/usr/bin/python3

# Beware, perl-like hackery ensues
# TODO: rewrite this with wic after moving to syslinux (grub / non-efi issues)


# TODO: this doesn't clean up if it errors mid way through
#       (loopbacks / mounts will remain open)

import sys
import os
import stat
import shutil
from glob import glob

# get wic.misc.get_bitbake_var for build variables
BB_PATHS = {}
BB_PATHS["basepath"] = os.path.join(os.path.dirname(__file__), "..", "..")
BB_PATHS["poky_scripts"] = os.path.join(BB_PATHS["basepath"], "scripts", "lib")
sys.path.append(BB_PATHS["poky_scripts"])
from wic.misc import get_bitbake_var


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


def get_fu_executables():
    fu_executables = {}

    work_dir = get_bitbake_var("WORKDIR")
    base_work_dir = os.path.join(work_dir, "../..")

    busybox_exec_glob = os.path.join(base_work_dir, "busyboxfu/*/busybox*/busybox")
    fu_executables["busybox"] = glob(busybox_exec_glob)[0]

    e2fsck_exec_glob = os.path.join(base_work_dir, "e2fsprogsfu/*/build/e2fsck/e2fsck")
    print(e2fsck_exec_glob)
    fu_executables["e2fsck"] = glob(e2fsck_exec_glob)[0]

    lrz_exec_glob = os.path.join(base_work_dir, "lrzszfu/*/image/usr/bin/lrz")
    fu_executables["lrz"] = glob(lrz_exec_glob)[0]

    lsz_exec_glob = os.path.join(base_work_dir, "lrzszfu/*/image/usr/bin/lsz")
    fu_executables["lsz"] = glob(lsz_exec_glob)[0]

    return fu_executables


def make_initramfs_dirs_and_empties(base_dir):
    for d in ["bin","sbin","etc","proc","sys","newroot","mnt",
            "usr/bin", "usr/sbin"]:
        next_dir = os.path.join(base_dir, "irf", d)
        os.makedirs(next_dir, exist_ok=True)

    for f in ["etc/mdev.conf", "etc/mtab"]:
        next_empty = os.path.join(base_dir, "irf", f)
        open(next_empty, "w").close()


def make_initramfs_simple_init(base_dir):
    init_contents = """#!/bin/sh

echo "running init"

echo "setting up busybox links..."
/bin/busybox --install -s

/bin/mknod /dev/null c 1 3
/bin/mknod /dev/tty c 5 0
/bin/mount -t proc none /proc
/bin/mount -t sysfs none /sys
/sbin/mdev -s

# mount stuff

echo "spawning a shell"
# this complains about no tty, need the console tty hack
exec /bin/busybox setsid cttyhack /bin/sh
"""
    init_filename = os.path.join(base_dir, "irf", "init")
    with open(init_filename, "w") as init_file:
        init_file.write(init_contents)
    os.chmod(init_filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
        stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def make_initramfs_images(base_dir):
    initramfs_path = os.path.join(base_dir, "irf")
    cpio_cmd = "cd %s && find . | cpio -H newc -o > ../initramfs.cpio" % (
        initramfs_path,)
    system_should_succeed(cpio_cmd)
    archive_cmd = "cd %s && cat initramfs.cpio | gzip -9 > initramfs.igz" % (
        base_dir,)
    system_should_succeed(archive_cmd)


def deploy_initramfs(fu_executables):
    # based on https://www.jootamam.net/howto-initramfs-image.htm
    work_dir = get_bitbake_var("WORKDIR")
    firmwareupdater_dir = os.path.join(work_dir, "../../../firmwareupdater")
    if os.path.exists(firmwareupdater_dir) == True:
        shutil.rmtree(firmwareupdater_dir)
    os.makedirs(firmwareupdater_dir, exist_ok=True)
    print("deploying in %s" % firmwareupdater_dir)

    make_initramfs_dirs_and_empties(firmwareupdater_dir)

    bin_dir = os.path.join(firmwareupdater_dir, "irf", "bin")
    shutil.copy(fu_executables["busybox"], bin_dir)
    sh_ln_cmd = "cd %s && ln -s busybox sh" % bin_dir
    system_should_succeed(sh_ln_cmd)
    shutil.copy(fu_executables["lrz"], bin_dir)
    shutil.copy(fu_executables["lsz"], bin_dir)

    sbin_dir = os.path.join(firmwareupdater_dir, "irf", "sbin")
    shutil.copy(fu_executables["e2fsck"], sbin_dir)

    make_initramfs_simple_init(firmwareupdater_dir)
    make_initramfs_images(firmwareupdater_dir)


if __name__ == "__main__":
    system_should_succeed(
        "bitbake busyboxfu e2fsprogsfu lrzszfu -c do_compile -c do_install")
    # find the firmware update executables needed
    fu_executables = get_fu_executables()
    deploy_initramfs(fu_executables)

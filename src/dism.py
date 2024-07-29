import sys
import logging
import threading
import subprocess
from pathlib import Path
from datetime import datetime

ENCODING = "850"


def _exec(cmd, stdout_log=Path("_log/dism_stdout.log"), dism_log=Path("_log/dism_verbose.log")):
    args = ["dism"] + [c for c in cmd if c is not None] + [f"/LogPath:{dism_log.absolute()}"]
    
    for logfile in (stdout_log, dism_log):
        with open(logfile, "a") as f:
            f.write(str(datetime.now()) + "  >>  " + " ".join(args) + "\n")

    res = subprocess.run(args, capture_output=True)
    
    with open(stdout_log, "a") as f:
        stdout = res.stdout.decode(ENCODING, errors="ignore")
        for line in stdout.splitlines():
            if (l := line.strip()) and (l[0] != "[" and l[-1] != "]"):
                f.write("    " + l + "\n")
        f.write("\n\n")

    with open(dism_log, "a") as f:
        f.write("\n\n")

    return res.stdout


def get_image_info(wim_file):
    logging.info(f"  Listing images in {wim_file}")
    res = _exec(
        [
            '/Get-WimInfo',
            f'/WimFile:{wim_file.absolute()}',
        ]
    )
    images = []
    for block in res.split(b"\r\n\r\n")[2:-1]:
        info = {}
        for line in block.splitlines():
            k, v = line.decode(ENCODING, errors="ignore").split(" ", maxsplit=1)
            info[k.strip(":")] = v.strip('"')
        images.append(info)
    return images


def mount_image(wim_file, index, mount_dir):
    logging.info(f"  Mounting {wim_file}::{index} at {mount_dir}")
    _exec(
        [
            '/Mount-Image',
            f'/ImageFile:{wim_file.absolute()}',
            f'/Index:{index}',
            f'/MountDir:{mount_dir.absolute()}',
        ]
    )


def unmount_image(mount_dir, commit):
    logging.info(f"  Unmounting {mount_dir}")
    _exec(
        [
            '/Unmount-Image',
            f'/MountDir:{mount_dir.absolute()}',
            '/Commit' if commit else "/Discard",
        ]
    )


def add_package(mount_dir, package):
    logging.info(f"    Adding package {package} to {mount_dir}")
    _exec(
        [
            f'/Image:{mount_dir.absolute()}',
            '/Add-Package',
            f'/PackagePath:{package.absolute()}',
        ]
    )


def add_appx(mount_dir, appx, license):
    logging.info(f"    Adding appx {appx} to {mount_dir}")
    _exec(
        [
            f'/Image:{mount_dir.absolute()}',
            '/Add-ProvisionedAppxPackage',
            f'/PackagePath:{appx.absolute()}',
            f'/LicensePath:{license.absolute()}',
        ]
    )


def export_image(wim_source, index, wim_target):
    logging.info(f"  Exporting {wim_source} to {wim_target}::{index}")
    _exec(
        [
            '/Export-Image',
            f'/SourceImageFile:{wim_source.absolute()}',
            f'/SourceIndex:{index}',
            f'/DestinationImageFile:{wim_target.absolute()}',
        ]
    )

def cleanup_image(mount_dir, reset_base=False, defer=False):
    logging.info(f"  Cleaning up {mount_dir}")
    _exec(
        [
            f'/image:{mount_dir.absolute()}',
            '/cleanup-image',
            '/StartComponentCleanup',
            '/ResetBase' if reset_base else None,
            '/Defer' if defer else None,
        ]
    )


def set_edition(mount_dir, edition, key):
    logging.info(f"  Setting Windows Edition to \"{edition}\"")
    _exec(
        [
            f'/Image:{mount_dir.absolute()}',
            f'/Set-Edition:{edition}',
            f'/ProductKey:{key}',
        ]
    )


def add_drivers(mount_dir, driver_dir, recurse=True, force_unsigned=True):
    logging.info(f"  Adding Drivers from {driver_dir} to {mount_dir}")
    _exec(
        [
            '/Add-Driver',
            f'/Image:{mount_dir.absolute()}',
            f'/Driver:{driver_dir.absolute()}',
            "/Recurse" if recurse else None,
            "/ForceUnsigned" if force_unsigned else None,
        ]
    )


def test():
    print(get_image_info("D:\windows-2021-ltsc-iso-refresh\_build\iso_data\sources\install.wim"))



if __name__ == "__main__":
    test()
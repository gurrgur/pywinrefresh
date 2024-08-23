import logging
import subprocess
from pathlib import Path
import shutil
from itertools import chain
import json
import os
import sys

import wget

import dism
import windows_update_catalog as wuc



def download_cached(url, cachedir):
    file_name = url.rsplit("/", maxsplit=1)[-1]
    if not (cachedir / file_name).is_file():
        logging.info(f"    downloading: {file_name}")
        wget.download(l, out=str(cachedir / file_name))
        print()
    else:
        logging.info(f"    cache hit: {file_name}")
    return file_name


# clean logs
logdir = Path("_log")
if not logdir.is_dir():
    logdir.mkdir()
for logfile in ("build.log", "dism_verbose.log", "dism_stdout.log"):
    open(logdir / logfile, "w").close()  # delete content

# set up logging
logfmt, datefmt = '%(asctime)s  %(message)s', '%H:%M:%S'
logging.basicConfig(level=logging.INFO, format=logfmt, datefmt=datefmt)
formatter = logging.Formatter(logfmt, datefmt=datefmt)
file_handler = logging.FileHandler('_log/build.log')
file_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_handler)

# log exceptions to file
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_exception


logging.info("Starting build: Windows 10 IoT Enterprise LTSC 2021 de-de")
logging.info("----------------------------------------------------------")
logging.info("Creating build directory.")
builddir = Path("_build")
if builddir.is_dir():
    try:
        shutil.rmtree(builddir)
    except:
        logging.info("Cleaning up previous wim mounts.")
        mounts = [
            builddir / "mount/main_os",
            builddir / "mount/win_re",
            builddir / "mount/win_pe",
        ]
        for mount in mounts:
            dism.unmount_image(mount, commit=False)
        shutil.rmtree(builddir)
builddir.mkdir()
pkgdir = builddir / "packages"
pkgdir.mkdir()
(pkgdir / "ndp").mkdir()

cachedir = Path("_cache")
if not cachedir.is_dir():
    cachedir.mkdir()

logging.info("Getting Updates from Windows Update Catalog.")
queries = {
    "lcu": "-Dynamic Cumulative Update for Windows 10 Version 21H2 for x64-based Systems",
    "ssu": "Servicing Stack Windows 10 Version 21H2 for x64",
    "ndp": "-Dynamic Cumulative Update for .NET Framework 3.5, 4.8 and 4.8.1 for Windows 10 Version 21H2 for x64"
}
ndp_packages = []
lcu_date = ""
for t, q in queries.items():
    try:
        logging.info(f"  query: \"{q}\"")
        latest_update = wuc.query(q)
        if t == "lcu":
            lcu_date = latest_update.Title.split(" ", maxsplit=1)[0]
        links = wuc.get_download_urls(latest_update.guid)
        for i, l in enumerate(links):
            file_name = download_cached(l, cachedir)
            if t == "ndp":
                ndp_label = file_name.rsplit("-")[-1].split("_")[0]
                ndp_packages.append(ndp_label)
                (pkgdir / f"{ndp_label}.msu").hardlink_to(cachedir / file_name)
            else:
                (pkgdir / f"{t}.msu").hardlink_to(cachedir / file_name)
                
    except Exception as e:
        raise e
    
iso_url = "https://drive.massgrave.dev/de-de_windows_10_enterprise_ltsc_2021_x64_dvd_71796d33.iso"
logging.info(f"Getting ISO from MAS ({iso_url})")
iso_name = download_cached(iso_url, cachedir)
iso_file = cachedir / iso_name
if not iso_file.is_file():
    logging.info(f"  Download failed. Searching for ISOs in {Path("iso").absolute()}")
    if Path("iso").is_dir() and (isos := list(Path("iso").glob("*.iso"))):
        iso_file = isos[0]
        logging.info(f"  Found {iso_file.absolute()}")
    else:
        logging.info(f"  No iso found! Aborting.")
        sys.exit()
(builddir / "base.iso").hardlink_to(iso_file)

logging.info("Extracting Windows Distribution.")
# subprocess.run("7z x -o_build\\iso_data _build\\base.iso".split(" "))
subprocess.run("7z x -o_build\\iso_data _build\\base.iso".split(" "), capture_output=True)

# Declare folders for mounted images and temp files
iso_data = builddir / "iso_data"
working_path = builddir / "tmp"
main_os = builddir / "mount/main_os"
win_re = builddir / "mount/win_re"

# Create folders for mounting images and storing temporary files
for p in [working_path, main_os, win_re]:
    if not p.is_dir():
        p.mkdir(parents=True)

logging.info("Automating Windows Setup.")
autounattend = Path("rsc/autounattend.xml")
if autounattend.is_file():
    logging.info(f"  using {autounattend.absolute()}")
    shutil.copyfile(autounattend, iso_data / "autounattend.xml")
else:
    logging.info(f"  autounattend.xml not found in {Path("rsc").absolute()}")

logging.info("Modifying Windows Image.")
install_wim = iso_data / "sources/install.wim"
image_info = dism.get_image_info(install_wim)
logging.info("  Found Images:")
for i in image_info:
    print(json.dumps(i))

image_info = filter(lambda info: info["Name"] == "Windows 10 Enterprise LTSC", image_info)
for tgt_idx, info in enumerate(image_info):
    src_idx, tgt_idx = info["Index"], str(tgt_idx + 1)
    dism.mount_image(install_wim, src_idx, main_os)
    dism.set_edition(main_os, edition="IoTEnterpriseS", key="QPM6N-7J2WJ-P88HH-P3YRH-YY74H")
    
    logging.info("Installing System Updates.")
    for pkg in ["ssu.msu", "lcu.msu"] + [n + ".msu" for n in ndp_packages]:
        dism.add_package(main_os, pkgdir / pkg)

    logging.info("Installing Drivers.")
    driver_dir = Path("rsc") / "drivers"
    if driver_dir.is_dir():
        dism.add_drivers(main_os, driver_dir, recurse=True, force_unsigned=True)
    else:
        logging.info("  {driver_dir} not found. No drivers will be installed.")
        
    logging.info("Finalizing Windows Image.")
    dism.cleanup_image(main_os, reset_base=False, defer=False)
    dism.unmount_image(main_os, commit=True)
    dism.export_image(iso_data / "sources" / "install.wim", tgt_idx, working_path / "install2.wim")
shutil.move(working_path / "install2.wim", iso_data / "sources/install.wim")

logging.info("Creating Modified Windows Distribution ISO.")
if not Path("_out").is_dir():
    Path("_out").mkdir()
subprocess.run([
    'oscdimg',
    '-bootdata:2#p0,e,b_build\\iso_data\\boot\\etfsboot.com#pEF,e,b_build\\iso_data\\efi\\microsoft\\boot\\efisys.bin',  # multi-boot (UEFI+legacy)
    '-o',  # optimize
    '-m',  # ignore maximum permitted iso size
    '-u2',  # file system
    '-udfver102',  # file system version
    f'-l"Win10IoTEnterprise2021"',  # volume label
    '_build\\iso_data',  # input directory
    f'_out\\de-de_windows_10_iot_enterprise_ltsc_2021_x64_update_{lcu_date}.iso',  # output iso
])

iso_final = Path("_out") / f'de-de_windows_10_iot_enterprise_ltsc_2021_x64_update_{lcu_date}.iso'
logging.info(f"Done: {iso_final.absolute()}.")

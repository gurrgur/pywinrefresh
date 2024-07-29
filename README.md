# pyWinRefresh

pyWinRefresh can be used to create a localized and up-to-date Windows 10 IoT Enterprise LTSC 2021 ISO. Currently only german localization is supported.

## Motivation

Starting October 2025, many Windows 10 editions will ceise to receive any further updates. A viable replacement for this pending deprecation is the Windows 10 IoT Enterprise LTSC 2021 edition, which will receive updates until January 2032. Unfortunetely, the IoT edition ISO is neither updated regularly, nor available in any languages except en-US. pyWinRefresh solves this by searching, downloading and offline-installing recent updates, and adding language support to the IoT ISO.

## Requirements

- Windows 10 PC with chocolatey package manager.
    - It is recommended to use a single-purpose virtual machine for pyWinRefresh.

## Setup

1. Double click `install-1-deps.bat`. This will install python, 7zip and Windows ADK using chocolatey.
2. Double click `install-2-venv.bat`. This will install the python dependencies into the virtual environment `_env`.
3. Reboot. This is needed for PATH to update properly, so that Windows ADK becomes available.

## Usage

- (optional) Put drivers into `rsc/drivers`. The drivers will be searched recursively in the folder and its subfolders, and installed during the ISO build process.
- Simply double click `run.bat`. This will:
    - Download the latest updates
    - Extract the base iso
    - Install the updates
    - Build the refreshed iso and save it in `_out`

## About Windows Offline updates

- There are 4 types of updates that can be installed
    1. **ssu**: Servicing stack update. The latest servicing stack needs to be installed before applying the latest cumulative update. The release cycle is irregular (every few months).
    2. **lcu**: Latest cumulative update. This bundles all regular updates and is released monthly.
    3. **ndp**: Latest .NET cumulative update. Released regularly (monthly?). For now the 4.8 Update is installed. For potential future .NET versions, you might have to adjust the search string used to query Microsoft Update Catalog defined in `src\build_iso.py::queries["ndp"]` and adjust the `ndp_select` variable appropriately.
    4. Windows Defender definition updates. This seems to not be available from Windows Update Catalog, hence is not included here.

- The general windows offline update procedure is as follows
    1. Extract the base iso files.
    2. Mount the extracted wim (per image: main os, recovery environment)
    3. Install Updates to mounted wim
    4. Unmount wim while saving changes
    5. Build the new Windows ISO with the updated files. This requires oscdimg.exe from Windows ADK.

## About Language Support

- The official iso for Windows 10 IoT Enterprise LTSC 2021 is only available with en-US language support.
- According to the MDL user who also provides [LTSC 2021 IOT Update Download Links](https://forums.mydigitallife.net/threads/discussion-windows-10-final-build-19041-19045-pc-20h1-22h2-vb_release.80763/page-16#post-1571109), the easiest way to add languages to the IoT Windows distribution is to **convert Enterprise LTSC to IoT Enterprise LTSC** by changing the edition key, rather than installing language packs to the en-US IoT distribution.

## Useful Links

- [Windows Multilingual; add lang](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/add-multilingual-support-to-windows-setup?view=windows-11#step-4-add-language-packs-to-the-windows-image)
[dism language settings](https://learn.microsoft.com/de-de/windows-hardware/manufacture/desktop/dism-languages-and-international-servicing-command-line-options?view=windows-11)
- [Windows Media Dynamic Update](https://learn.microsoft.com/de-de/windows/deployment/update/media-dynamic-update)
- [LTSC 2021 IOT Update Download Links](https://forums.mydigitallife.net/threads/discussion-windows-10-final-build-19041-19045-pc-20h1-22h2-vb_release.80763/page-16#post-1571109)
  - **according to the author of this post, it is easier to convert de-ltsc to de-iot-ltsc, rather than en-iot-ltsc to de-iot-ltsc**!
- [image servicing](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/servicing-the-image-with-windows-updates-sxs?view=windows-10)
- [iot ent deploy](https://github.com/ms-iot/windows-iotent-deploy)
- [needed updates + dotnet langpack update](https://forums.mydigitallife.net/threads/discussion-windows-10-enterprise-iot-enterprise-n-ltsc-2021.84509/page-203#post-1843620)
- [langpack iso 21h2 ltsc](https://forums.mydigitallife.net/threads/discussion-windows-10-enterprise-iot-enterprise-n-ltsc-2021.84509/page-193#post-1825828)
- [msdocs localization packages](https://learn.microsoft.com/en-us/windows-365/enterprise/provide-localized-windows-experience)
- [msdocs image with custom localization](https://learn.microsoft.com/en-us/windows-365/enterprise/create-custom-image-languages)
- [langpack installation](https://learn.microsoft.com/en-us/azure/virtual-desktop/language-packs)]
- [media refresh](https://learn.microsoft.com/de-de/windows/iot/iot-enterprise/deployment/media-refresh)
- [Slipstreaming Proxmox VirtIO Drivers](https://github.com/Zer0CoolX/proxmox-windows-slipstream-virtio-drivers/blob/master/README.md)
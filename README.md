# sxsc
A fork of [`echnobas`/sxsc](https://github.com/echnobas/sxsc) (the SxS compiler - pronounced sxs-see) for use in automatic package building for [Atlas](https://github.com/Atlas-OS/Atlas/tree/main/src/sxsc) and RapidOS.

GNU General Public License v3.0 [license](https://github.com/echnobas/sxsc/blob/a45c5f321153a0dd33266cb35fce3effac7212ad/LICENSE).

### He3als Changes
- Removed [`gullible_installer.ps1`](https://github.com/echnobas/sxsc/blob/master/gullible_installer.ps1)
  - Not needed for building
  - [`online-sxs.cmd`](https://github.com/he3als/online-sxs) is used instead
- Removed binaries
  - They are included [by default](https://github.com/actions/runner-images/blob/main/images/win/Windows2022-Readme.md#installed-windows-sdks) in the `windows-latest` GitHub Action runner
  - Changed in the Python script to match that
  - Removed binaries:  `makecab, makecat, signtool`, use Windows Kit
- Add `requirements.txt`
- Files support

### Instead1337 Changes
- Enhanced `sxsc.py` for better usability by adding a search for any configuration files that start with `cfg` and end with `.yaml`. If multiple files are found, a file explorer prompts the user to select one.
- In `build.ps1` implemented a smart system to locate Windows Kit subfolders containing Windows build names, along with various qol improvements.
And other little changes...

>[!Important]
> To use the `sxsc` method, you need to have the Windows Kit, a configuration file (such as the [AtlasOS Configuration File](https://github.com/Atlas-OS/Atlas/tree/main/src/sxsc)), and a bit of expertise.
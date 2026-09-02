# SHP2KMZ Tool

![Version](https://img.shields.io/badge/version-2.4-blue)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
![Distribution](https://img.shields.io/badge/distribution-binary_only-64748B)
![Format](https://img.shields.io/badge/input-SHP-289C8E)
![Format](https://img.shields.io/badge/output-KMZ-289C8E)

**English | [简体中文](README_ZH.md)**

Batch Shapefile-to-KMZ conversion for field survey preparation.

**SHP2KMZ Tool** (外业调查批量SHP转KMZ工具) is a packaged Windows application developed in Python for converting Shapefile data into KMZ files. It is designed for field-survey data preparation and batch conversion workflows. This repository provides the author's v2.4 application package and bilingual usage notes; the complete Python source code is not publicly released.

> **[Download SHP2KMZ Tool v2.4 — Windows RAR package](https://github.com/zhangyhrs/SHP2KMZ_Tool/raw/refs/heads/main/downloads/SHP2KMZ_Tool_v2.4.rar)**
>
> Extract the entire archive before running the application. Do not download GitHub's “Code → Download ZIP” as a substitute for the application package.

## Overview

- Prepare KMZ data from Shapefiles for field survey use.
- Batch-conversion workflow for repeated SHP-to-KMZ processing.
- Windows executable distributed with its supporting runtime files.
- Developed in Python and distributed as a compiled Windows application.
- No separate Python installation is intended for this packaged distribution; actual compatibility should be checked on your Windows computer.

## Quick start

1. Download the RAR package above and extract **all files** to a local folder.
2. Keep the executable, DLLs, and bundled subfolders together.
3. Start `0shp_to_kmz_2.4.exe`.
4. Use the application's controls to select your Shapefile input and output location, then start conversion.
5. Open the resulting KMZ in your intended viewer and check feature counts, location, attributes and display before field deployment.

Start with a small, non-sensitive test dataset. The executable has not been run or functionally validated in this repository publishing process.

## Prepare your data

- Keep matching `.shp`, `.shx` and `.dbf` files together. Retain `.prj` and `.cpg` files when available.
- Confirm the source coordinate reference system. Do not guess a CRS merely to make the data appear on a map.
- Work from a copy and use a separate output folder.
- Inspect the KMZ in the actual target application; coordinate handling and display can differ between viewers.

## Download verification

| Item | Value |
|---|---|
| Version | 2.4 |
| Package | `SHP2KMZ_Tool_v2.4.rar` |
| Size | 25,903,513 bytes (about 24.70 MiB) |
| Entry point | `0shp_to_kmz_2.4.exe` |

The archive is the original supplied package with a download-friendly filename; its contents have not been modified. See [SHA-256 checksum](downloads/SHA256SUMS.txt).

In PowerShell:

```powershell
Get-FileHash .\SHP2KMZ_Tool_v2.4.rar -Algorithm SHA256
```

A matching checksum confirms file integrity, not malware safety or functional correctness.

## Troubleshooting

- **Missing DLL or application cannot start:** extract the complete package and keep the directory structure intact.
- **Misplaced features:** check source CRS information and the coordinate interpretation of your target viewer.
- **Unreadable attribute text:** check the input encoding and associated `.cpg` file.
- **Security warning:** check the download source and scan the file. Do not disable antivirus protection to run it.

For bug reports, use [Issues](https://github.com/zhangyhrs/SHP2KMZ_Tool/issues) and include the application version, Windows version, reproduction steps and a redacted screenshot. Do not post confidential survey data, credentials or personal information.

## Distribution & license notice

This is a **compiled application distribution**, not a publication of the tool's complete Python source code. Public access to the repository or application package does not by itself grant an open-source software license. Bundled third-party components remain subject to their own licenses and notices.

See **[Software Distribution & License Notice](LICENSE_NOTICE.md)** for the repository's software-distribution boundary and user responsibilities regarding source geospatial data.

## Project links

[Changelog](CHANGELOG.md) · [License notice](LICENSE_NOTICE.md) · [Report an issue](https://github.com/zhangyhrs/SHP2KMZ_Tool/issues)

## Follow & Connect

Follow **测绘地信** for surveying, remote sensing and GIS content, or visit the **测绘地理信息共享中心** Knowledge Planet community. Click an image to view it at full size.

<table>
  <tr>
    <th width="50%">WeChat Official Account<br>测绘地信</th>
    <th width="50%">Knowledge Planet<br>测绘地理信息共享中心</th>
  </tr>
  <tr>
    <td align="center" valign="middle"><a href="assets/wechat-official-account.png"><img src="assets/wechat-official-account.png" alt="微信公众号：测绘地信" height="140"></a></td>
    <td align="center" valign="middle"><a href="assets/knowledge-planet.jpg"><img src="assets/knowledge-planet.jpg" alt="知识星球：测绘地理信息共享中心" height="140"></a></td>
  </tr>
</table>

## Author

**Zhang Y.H.** · GitHub [@zhangyhrs](https://github.com/zhangyhrs)

Related: [GeoStar Selector for QGIS](https://github.com/zhangyhrs/GeoStar-Selector-QGIS) · [Map Tile Downloader](https://github.com/zhangyhrs/map_tile_downloader)

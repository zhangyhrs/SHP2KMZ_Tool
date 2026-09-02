# SHP2KMZ Tool｜外业调查批量 SHP 转 KMZ 工具

![Version](https://img.shields.io/badge/version-2.4-blue)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
![Distribution](https://img.shields.io/badge/distribution-binary_only-64748B)
![Format](https://img.shields.io/badge/input-SHP-289C8E)
![Format](https://img.shields.io/badge/output-KMZ-289C8E)

**[English](README.md) | 简体中文**

面向外业调查数据准备的批量 SHP 转 KMZ 工具。

**外业调查批量 SHP 转 KMZ 工具**是一款采用 Python 开发并打包发布的 Windows 桌面程序，用于将 Shapefile 数据批量转换为 KMZ 文件，重点服务于外业调查、数据携带和成果快速浏览。本仓库提供作者发布的 v2.4 Windows 程序包及中英文使用说明，完整 Python 源码不公开发布。

> **[直接下载 SHP2KMZ Tool v2.4 — Windows RAR 程序包](https://github.com/zhangyhrs/SHP2KMZ_Tool/raw/refs/heads/main/downloads/SHP2KMZ_Tool_v2.4.rar)**
>
> 下载后完整解压再运行。不要用仓库“Code → Download ZIP”代替程序包下载入口。

## 工具概述

- 面向外业调查的数据准备，将 SHP 数据转换为 KMZ。
- 支持面向重复任务的批量 SHP → KMZ 转换流程。
- 采用 Python 开发，并以 Windows 打包程序形式发布。
- EXE 与配套运行文件一起分发，使用时应保留完整目录结构。
- 打包版按无需单独安装 Python 的方式分发；具体系统兼容性需在本机验证。

## 快速使用

1. 点击上方链接下载 RAR 程序包，完整解压到本地文件夹。
2. 保留 EXE、DLL 和所有配套子文件夹，不要只复制 EXE。
3. 双击运行 `0shp_to_kmz_2.4.exe`。
4. 按程序界面选择 SHP 输入数据及输出位置，启动转换。
5. 在实际使用的地图软件中打开输出 KMZ，检查要素数量、空间位置、属性和显示效果，再用于外业。

建议先用少量、不涉密的数据测试。本次仓库整理未在 Windows 环境运行该 EXE，不代表已完成软件功能和兼容性测试。

## 数据准备

- 同名 `.shp`、`.shx`、`.dbf` 文件应完整放在一起；有 `.prj`、`.cpg` 时也请保留。
- 确认源数据坐标系，不要为使图形显示而随意指定坐标系。
- 使用原始数据的副本，并设置独立输出目录。
- 在实际目标软件中检查 KMZ；不同软件的坐标处理和显示可能存在差异。

## 下载与校验

| 项目 | 内容 |
|---|---|
| 版本 | 2.4 |
| 程序包 | `SHP2KMZ_Tool_v2.4.rar` |
| 文件大小 | 25,903,513 字节，约 24.70 MiB |
| 启动文件 | `0shp_to_kmz_2.4.exe` |

上传的是原始程序包，仅使用便于下载的文件名，包内文件未经修改。校验值见 [SHA-256 校验文件](downloads/SHA256SUMS.txt)。

在 PowerShell 中执行：

```powershell
Get-FileHash .\SHP2KMZ_Tool_v2.4.rar -Algorithm SHA256
```

校验值一致只能证明文件内容一致，不代表病毒扫描或功能测试通过。

## 常见问题

- **缺少 DLL、无法启动：**检查是否完整解压，是否保持原有目录结构。
- **位置偏移：**检查源数据坐标系信息及目标地图软件的坐标解释。
- **属性乱码：**检查输入数据编码及配套 `.cpg` 文件。
- **安全软件提示：**核对下载来源并扫描文件，不建议关闭安全防护强行运行。

如需反馈问题，请在 [Issues](https://github.com/zhangyhrs/SHP2KMZ_Tool/issues) 中说明程序版本、Windows 版本、复现步骤，并提供脱敏截图。请勿公开涉密测绘资料、账号凭据或个人信息。

## 分发与授权说明

本仓库用于发布**已打包的可执行程序**，不等于公开该工具的完整 Python 源码。仓库公开访问或程序包可以下载，也不等同于自动授予开源许可证项下的修改、再分发等权利；程序包内第三方组件仍分别适用各自许可证及声明。

详细说明见 **[软件分发与授权说明](LICENSE_NOTICE.md)**，其中同时明确了源地理空间数据的使用责任边界。

## 项目入口

[更新记录](CHANGELOG.md) · [授权说明](LICENSE_NOTICE.md) · [问题反馈](https://github.com/zhangyhrs/SHP2KMZ_Tool/issues)

## 关注与交流

欢迎关注微信公众号 **测绘地信**，获取遥感、测绘与 GIS 技术内容；也可访问知识星球 **测绘地理信息共享中心**，交流软件工具与专业资料。点击图片可查看原图。

<table>
  <tr>
    <th width="50%">微信公众号<br>测绘地信</th>
    <th width="50%">知识星球<br>测绘地理信息共享中心</th>
  </tr>
  <tr>
    <td align="center" valign="middle"><a href="assets/wechat-official-account.png"><img src="assets/wechat-official-account.png" alt="微信公众号：测绘地信" height="140"></a></td>
    <td align="center" valign="middle"><a href="assets/knowledge-planet.jpg"><img src="assets/knowledge-planet.jpg" alt="知识星球：测绘地理信息共享中心" height="140"></a></td>
  </tr>
</table>

## 作者

**Zhang Y.H.** · GitHub [@zhangyhrs](https://github.com/zhangyhrs)

相关工具：[GeoStar Selector for QGIS](https://github.com/zhangyhrs/GeoStar-Selector-QGIS) · [Map Tile Downloader](https://github.com/zhangyhrs/map_tile_downloader)

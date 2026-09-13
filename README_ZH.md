# SHP2KMZ Tool｜外业调查批量 SHP 转 KMZ 工具

![Version](https://img.shields.io/badge/version-2.5.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
![Language](https://img.shields.io/badge/language-Python-3776AB?logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-PyQt5-41CD52)
![License](https://img.shields.io/badge/license-GPL--3.0-green)
![Format](https://img.shields.io/badge/input-SHP-289C8E)
![Format](https://img.shields.io/badge/output-KMZ-289C8E)

**[English](README.md) | 简体中文**

面向外业调查、自然资源调查和 GIS 数据快速浏览的批量 SHP → KMZ 桌面工具。

**SHP2KMZ Tool V2.5.0** 采用 Python + PyQt5 开发，在保留 V2.4 批量转换、字段着色、分组导出和图斑标注等功能的基础上，对界面、符号系统和标注位置进行了重构，并从 V2.5.0 起公开 Python 源代码。

> **源码：[`SHP2KMZ_Tool_V2.5.0.py`](SHP2KMZ_Tool_V2.5.0.py)**  
> **历史打包版：[`SHP2KMZ_Tool_v2.4.rar`](downloads/SHP2KMZ_Tool_v2.4.rar)**

## 主要功能

- **批量转换**：支持选择单个、多个 SHP 或整个文件夹，批量输出 KMZ。
- **坐标处理**：读取源空间参考并转换至 CGCS2000 地理坐标系；兼容 GDAL 3+ 轴顺序。
- **边线样式**：可设置线宽和默认颜色。
- **字段分组着色**：按指定字段值设置不同边线颜色。
- **字段分组导出**：按字段值分别生成 KMZ，命名为“原SHP名_分组值_数量.kmz”。
- **图斑标注**：可设置标注字段、字号、字体颜色。
- **标注符号**：内置基础符号、调查标记和提示符号，可设置符号颜色和大小。
- **离线符号**：符号动态生成 PNG 并写入 KMZ，不依赖在线图标。
- **标注位置**：支持自动推荐、几何质心、面内点、外接矩形中心和顶点平均中心。
- **后台处理**：使用 QThread 执行转换，提供进度和运行日志。

## V2.5.0 重点更新

V2.5.0 将 GUI 从旧版界面重构为 PyQt5，同时保留 V2.4 的核心能力，并增加：

- 现代化、可滚动的响应式界面；
- 可视化符号库；
- 符号颜色和大小设置；
- 符号随 KMZ 本地打包；
- 多种标注位置算法；
- 版权信息在源码和界面中统一显示；
- 完整 Python 源代码公开。

## 源码运行

### 环境

建议使用 Python 3.8+。主要依赖：

```text
PyQt5
GDAL
```

GDAL 建议通过 Conda/OSGeo 环境安装，以确保本地 GDAL 与 Python 绑定版本一致。

### 运行

将 `icon.png` 放在程序源码同目录（可选；不存在时程序仍可运行），然后执行：

```bash
python SHP2KMZ_Tool_V2.5.0.py
```

## 数据要求

Shapefile 建议至少保持以下同名文件完整：

```text
.shp
.shx
.dbf
```

如有 `.prj`、`.cpg` 也应保留。坐标系信息不明确时请先核实，不建议为了“能显示”而随意指定坐标系。

## 历史 Windows 程序包

仓库仍保留 V2.4 Windows RAR 程序包，便于旧版本用户继续使用：

[`downloads/SHP2KMZ_Tool_v2.4.rar`](downloads/SHP2KMZ_Tool_v2.4.rar)

该文件作为历史版本保留，V2.5.0 的主要开发基线为公开源码。

## 许可证与版权

Copyright (c) 2026 Zhang Y.H.

本项目 V2.5.0 源代码按 **GNU General Public License v3.0 (GPL-3.0)** 发布，详见 [LICENSE](LICENSE)。

第三方依赖仍分别适用其自身许可证；其中 PyQt5 的许可条件请以 Riverbank Computing 官方条款为准。项目中提及 ArcGIS/Esri 仅用于说明 GIS 符号库的交互风格，本项目未直接分发 ArcGIS/Esri 原始符号资源。

用户应自行确认待处理地理空间数据具有合法处理、复制、共享和发布权限，并遵守相应保密要求。

## 问题反馈

如发现问题，请通过 [Issues](https://github.com/zhangyhrs/SHP2KMZ_Tool/issues) 提交：

- 软件版本；
- Windows / Python / GDAL 版本；
- 问题复现步骤；
- 脱敏后的日志或截图。

请勿上传涉密测绘资料、账号凭据或个人敏感信息。

## 更新记录

详见 [CHANGELOG.md](CHANGELOG.md)。

## 关注与交流

欢迎关注微信公众号 **测绘地信**，也可访问知识星球 **测绘地理信息共享中心**。

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

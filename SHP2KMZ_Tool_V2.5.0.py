# -*- coding: utf-8 -*-
"""
外业调查批量 SHP 转 KMZ 工具 V2.5.0
PyQt5 现代化重构完整版

Copyright (c) 2026 Zhang Y.H.

设计原则
--------
1. 保留 V2.4 全部核心功能：
   - 文件夹 / 多文件 SHP 输入
   - 输出路径
   - 边线宽度与颜色
   - 按字段分组着色
   - 字段值颜色映射
   - 按字段分组导出 KMZ
   - 标注字段、字号、字体颜色
   - 标注符号、符号颜色、符号大小
   - 批量转换、进度、日志、帮助
2. GUI 使用 PyQt5 重构。
3. 主窗口图标读取程序当前目录下 icon.png。
4. 标注符号采用内置矢量绘制，不直接分发 ArcGIS/Esri 符号文件。
5. 符号自动写入 KMZ，可离线显示。
6. 标注点：
   - 质心在面内 -> 使用质心
   - 质心在面外 -> PointOnSurface
   - 异常 -> 包络框中心
7. 版本：V2.5.0
"""

import os
import sys
import glob
import math
import shutil
import tempfile
import zipfile
from collections import defaultdict
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from osgeo import ogr, osr

from PyQt5.QtCore import Qt, QSize, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import (
    QColor, QIcon, QPixmap, QPainter, QPen, QBrush,
    QPolygon, QFont
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QColorDialog, QComboBox, QCheckBox, QDoubleSpinBox,
    QProgressBar, QPlainTextEdit, QMessageBox, QDialog, QListWidget,
    QListWidgetItem, QDialogButtonBox, QScrollArea, QFrame,
    QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QSplitter,
    QSizePolicy
)


APP_NAME = "外业调查批量SHP转KMZ工具"
APP_VERSION = "V2.5.0"
SUPPORT_EMAIL = "zhangyhcumt@163.com"
COPYRIGHT_TEXT = "Copyright (c) 2026 Zhang Y.H."


# ============================================================
# 通用工具
# ============================================================

def application_dir():
    """返回脚本或 EXE 所在目录。"""
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def application_icon():
    return os.path.join(application_dir(), "icon.png")


def set_traditional_axis_order(srs):
    """
    GDAL 3+ 中 EPSG 可能采用纬度/经度轴顺序。
    对桌面 GIS/KML 统一采用传统 X=经度、Y=纬度。
    """
    if srs is None:
        return
    try:
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    except Exception:
        pass


def make_color_button_style(color):
    return (
        "QPushButton{"
        f"background-color:{color};"
        "border:1px solid #AAB4C2;"
        "border-radius:5px;"
        "}"
        "QPushButton:hover{border:1px solid #4F86C6;}"
    )


# ============================================================
# 符号库
# ============================================================

SYMBOL_LIBRARY = [
    ("无", "none", "基础符号"),
    ("实心圆", "circle", "基础符号"),
    ("空心圆", "circle_outline", "基础符号"),
    ("实心方形", "square", "基础符号"),
    ("空心方形", "square_outline", "基础符号"),
    ("三角形", "triangle", "基础符号"),
    ("倒三角", "triangle_down", "基础符号"),
    ("菱形", "diamond", "基础符号"),
    ("五角星", "star", "调查标记"),
    ("十字", "cross", "调查标记"),
    ("叉号", "x", "调查标记"),
    ("靶心", "target", "调查标记"),
    ("旗帜", "flag", "调查标记"),
    ("定位点", "pin", "调查标记"),
    ("感叹号", "warning", "提示符号"),
    ("信息点", "info", "提示符号"),
]


def _star_polygon(cx, cy, r_outer, r_inner):
    pts = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        pts.append(QPoint(
            int(cx + math.cos(angle) * r),
            int(cy + math.sin(angle) * r)
        ))
    return QPolygon(pts)


def render_symbol(symbol_key, color="#E53935", size=64):
    """
    使用 QPainter 动态生成符号。
    这些是本工具绘制的通用 GIS 风格符号，不依赖 ArcGIS 安装。
    """
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    c = QColor(color)
    dark = QColor("#263238")
    cx = size // 2
    cy = size // 2

    pen = QPen(c)
    pen.setWidth(max(2, size // 28))
    p.setPen(pen)
    p.setBrush(QBrush(c))

    r = max(8, size // 5)

    if symbol_key == "none":
        p.setPen(QColor("#7A8594"))
        f = p.font()
        f.setPointSize(max(9, size // 6))
        p.setFont(f)
        p.drawText(pix.rect(), Qt.AlignCenter, "无")

    elif symbol_key == "circle":
        p.drawEllipse(cx-r, cy-r, r*2, r*2)

    elif symbol_key == "circle_outline":
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx-r, cy-r, r*2, r*2)

    elif symbol_key == "square":
        p.drawRect(cx-r, cy-r, r*2, r*2)

    elif symbol_key == "square_outline":
        p.setBrush(Qt.NoBrush)
        p.drawRect(cx-r, cy-r, r*2, r*2)

    elif symbol_key == "triangle":
        pts = QPolygon([
            QPoint(cx, cy-r-2),
            QPoint(cx-r-2, cy+r),
            QPoint(cx+r+2, cy+r),
        ])
        p.drawPolygon(pts)

    elif symbol_key == "triangle_down":
        pts = QPolygon([
            QPoint(cx-r-2, cy-r),
            QPoint(cx+r+2, cy-r),
            QPoint(cx, cy+r+2),
        ])
        p.drawPolygon(pts)

    elif symbol_key == "diamond":
        pts = QPolygon([
            QPoint(cx, cy-r-3),
            QPoint(cx-r-3, cy),
            QPoint(cx, cy+r+3),
            QPoint(cx+r+3, cy),
        ])
        p.drawPolygon(pts)

    elif symbol_key == "star":
        p.drawPolygon(_star_polygon(cx, cy, r+4, max(4, r//2)))

    elif symbol_key == "cross":
        p.setBrush(Qt.NoBrush)
        p.drawLine(cx-r, cy, cx+r, cy)
        p.drawLine(cx, cy-r, cx, cy+r)

    elif symbol_key == "x":
        p.setBrush(Qt.NoBrush)
        p.drawLine(cx-r, cy-r, cx+r, cy+r)
        p.drawLine(cx+r, cy-r, cx-r, cy+r)

    elif symbol_key == "target":
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(cx-r-2, cy-r-2, (r+2)*2, (r+2)*2)
        p.drawEllipse(cx-r//2, cy-r//2, r, r)
        p.drawLine(cx-r-5, cy, cx+r+5, cy)
        p.drawLine(cx, cy-r-5, cx, cy+r+5)

    elif symbol_key == "flag":
        p.setBrush(Qt.NoBrush)
        p.drawLine(cx-r//2, cy+r+5, cx-r//2, cy-r-7)
        p.setBrush(QBrush(c))
        pts = QPolygon([
            QPoint(cx-r//2, cy-r-7),
            QPoint(cx+r, cy-r-3),
            QPoint(cx-r//2, cy+2),
        ])
        p.drawPolygon(pts)

    elif symbol_key == "pin":
        p.setBrush(QBrush(c))
        p.drawEllipse(cx-r, cy-r-5, r*2, r*2)
        pts = QPolygon([
            QPoint(cx-r+3, cy),
            QPoint(cx+r-3, cy),
            QPoint(cx, cy+r+10),
        ])
        p.drawPolygon(pts)
        p.setBrush(QBrush(QColor("white")))
        p.setPen(Qt.NoPen)
        p.drawEllipse(cx-r//3, cy-r//3-4, max(4, r*2//3), max(4, r*2//3))

    elif symbol_key == "warning":
        pts = QPolygon([
            QPoint(cx, cy-r-6),
            QPoint(cx-r-5, cy+r+4),
            QPoint(cx+r+5, cy+r+4),
        ])
        p.drawPolygon(pts)
        p.setPen(QPen(QColor("white"), max(2, size//28)))
        p.drawLine(cx, cy-r//2, cx, cy+r//3)
        p.drawPoint(cx, cy+r//2+2)

    elif symbol_key == "info":
        p.drawEllipse(cx-r-2, cy-r-2, (r+2)*2, (r+2)*2)
        p.setPen(QColor("white"))
        f = p.font()
        f.setBold(True)
        f.setPointSize(max(10, size//4))
        p.setFont(f)
        p.drawText(pix.rect(), Qt.AlignCenter, "i")

    else:
        p.setPen(dark)
        p.drawText(pix.rect(), Qt.AlignCenter, "?")

    p.end()
    return pix


class SymbolLibraryDialog(QDialog):
    """ArcGIS 风格交互思路的符号库，但使用本工具自绘符号。"""

    def __init__(self, current_key, color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("标注符号库")
        self.resize(690, 520)
        self.current_key = current_key
        self.symbol_color = color
        self.selected_key = current_key

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(8)

        header = QLabel("选择符号")
        header.setObjectName("dialogTitle")
        root.addWidget(header)

        tip = QLabel("按类别浏览常用点符号。双击符号可直接应用。")
        tip.setStyleSheet("color:#6B7280;")
        root.addWidget(tip)

        self.category_combo = QComboBox()
        categories = ["全部"] + list(dict.fromkeys(x[2] for x in SYMBOL_LIBRARY))
        self.category_combo.addItems(categories)
        self.category_combo.currentTextChanged.connect(self.refresh_items)
        root.addWidget(self.category_combo)

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(58, 58))
        self.list_widget.setGridSize(QSize(125, 105))
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setSpacing(8)
        self.list_widget.itemDoubleClicked.connect(self._double_click)
        root.addWidget(self.list_widget, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.refresh_items()

    def refresh_items(self):
        category = self.category_combo.currentText() or "全部"
        self.list_widget.clear()

        selected_item = None
        for name, key, cat in SYMBOL_LIBRARY:
            if category != "全部" and cat != category:
                continue
            item = QListWidgetItem(
                QIcon(render_symbol(key, self.symbol_color, 58)),
                name
            )
            item.setData(Qt.UserRole, key)
            item.setTextAlignment(Qt.AlignHCenter)
            self.list_widget.addItem(item)
            if key == self.current_key:
                selected_item = item

        if selected_item:
            self.list_widget.setCurrentItem(selected_item)

    def _accept(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_key = item.data(Qt.UserRole)
        self.accept()

    def _double_click(self, item):
        self.selected_key = item.data(Qt.UserRole)
        self.accept()


# ============================================================
# 字段颜色映射
# ============================================================

class ColorMappingDialog(QDialog):

    DEFAULT_COLORS = [
        "#E53935", "#1E88E5", "#43A047", "#FB8C00",
        "#8E24AA", "#00897B", "#6D4C41", "#3949AB",
        "#7CB342", "#F4511E"
    ]

    def __init__(self, field_name, values, mapping, parent=None):
        super().__init__(parent)
        self.setWindowTitle("字段值颜色映射")
        self.resize(560, 520)

        self.field_name = field_name
        self.mapping = dict(mapping)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)

        title = QLabel(f"字段：{field_name}")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        tip = QLabel("点击颜色块，为不同字段值设置边线颜色。")
        tip.setStyleSheet("color:#6B7280;")
        root.addWidget(tip)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(4, 4, 4, 4)
        body_layout.setSpacing(4)

        for i, value in enumerate(sorted(values)):
            value = str(value)
            self.mapping.setdefault(
                value,
                self.DEFAULT_COLORS[i % len(self.DEFAULT_COLORS)]
            )

            row = QWidget()
            lay = QHBoxLayout(row)
            lay.setContentsMargins(8, 4, 8, 4)

            lbl = QLabel(value)
            lbl.setMinimumWidth(280)

            btn = QPushButton()
            btn.setFixedSize(90, 30)
            btn.setStyleSheet(
                make_color_button_style(self.mapping[value])
            )

            def choose(checked=False, v=value, b=btn):
                c = QColorDialog.getColor(
                    QColor(self.mapping[v]),
                    self,
                    f"设置“{v}”颜色"
                )
                if c.isValid():
                    self.mapping[v] = c.name().upper()
                    b.setStyleSheet(
                        make_color_button_style(self.mapping[v])
                    )

            btn.clicked.connect(choose)

            lay.addWidget(lbl)
            lay.addWidget(btn)
            lay.addStretch()
            body_layout.addWidget(row)

        body_layout.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)


# ============================================================
# SHP -> KMZ 核心
# ============================================================

class ShpToKmzCore:

    def __init__(self, options, logger=None):
        self.options = options
        self.logger = logger or (lambda msg: None)

    def log(self, msg):
        self.logger(str(msg))

    @staticmethod
    def sanitize_filename(filename):
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        result = str(filename)
        for ch in invalid_chars:
            result = result.replace(ch, "_")
        result = result.strip().strip(".")
        return result or "未知"

    @staticmethod
    def hex_to_kml_color(hex_color):
        """
        #RRGGBB -> KML AABBGGRR
        """
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"ff{b:02x}{g:02x}{r:02x}"

    def detect_cgcs2000_projection(self, layer):
        """
        保留原 V2.4 自动识别思路。
        仅在无空间参考时尝试使用横坐标带号判断。
        """
        layer.ResetReading()
        feature = layer.GetNextFeature()

        if feature:
            geom = feature.GetGeometryRef()
            if geom:
                env = geom.GetEnvelope()
                x_center = (env[0] + env[1]) / 2
                zone = int(x_center / 1000000)

                if 13 <= zone <= 45:
                    epsg_code = 4534 + zone
                    try:
                        srs = osr.SpatialReference()
                        srs.ImportFromEPSG(epsg_code)
                        set_traditional_axis_order(srs)
                        self.log(
                            f"  自动识别为：{srs.GetName()} (EPSG:{epsg_code})"
                        )
                        layer.ResetReading()
                        return srs
                    except Exception:
                        pass

        layer.ResetReading()
        return None

    def get_transform(self, layer):
        source = layer.GetSpatialRef()

        if source is None:
            self.log("  未检测到坐标系，尝试自动识别 CGCS2000 投影...")
            source = self.detect_cgcs2000_projection(layer)

        target = osr.SpatialReference()
        target.ImportFromEPSG(4490)
        set_traditional_axis_order(target)

        if source:
            source = source.Clone()
            set_traditional_axis_order(source)

        if source and not source.IsSame(target):
            self.log(
                f"  坐标转换：{source.GetName()} -> CGCS2000 地理坐标系"
            )
            return osr.CoordinateTransformation(source, target)

        return None

    @staticmethod
    def create_kml_structure():
        kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
        document = SubElement(kml, "Document")
        return kml, document

    def add_polygon_geometry(self, parent, polygon):
        kml_polygon = SubElement(parent, "Polygon")
        SubElement(kml_polygon, "extrude").text = "0"
        SubElement(kml_polygon, "altitudeMode").text = "clampToGround"

        outer_boundary = SubElement(kml_polygon, "outerBoundaryIs")
        ring_node = SubElement(outer_boundary, "LinearRing")
        coords = SubElement(ring_node, "coordinates")

        ring = polygon.GetGeometryRef(0)
        coord_list = []
        for i in range(ring.GetPointCount()):
            x, y, _ = ring.GetPoint(i)
            coord_list.append(f"{x},{y},0")
        coords.text = " ".join(coord_list)

        for i in range(1, polygon.GetGeometryCount()):
            inner_ring = polygon.GetGeometryRef(i)
            inner_boundary = SubElement(kml_polygon, "innerBoundaryIs")
            ring_node = SubElement(inner_boundary, "LinearRing")
            coords = SubElement(ring_node, "coordinates")

            coord_list = []
            for j in range(inner_ring.GetPointCount()):
                x, y, _ = inner_ring.GetPoint(j)
                coord_list.append(f"{x},{y},0")
            coords.text = " ".join(coord_list)

    def add_geometry(self, parent, geometry):
        geom_type = geometry.GetGeometryName().upper()

        if geom_type == "POLYGON":
            self.add_polygon_geometry(parent, geometry)

        elif geom_type == "MULTIPOLYGON":
            multi = SubElement(parent, "MultiGeometry")
            for i in range(geometry.GetGeometryCount()):
                self.add_polygon_geometry(
                    multi,
                    geometry.GetGeometryRef(i)
                )

        else:
            raise ValueError(f"当前仅支持面要素，检测到：{geom_type}")

    def add_polygon_to_kml(self, document, geometry, name, color):
        folder = None

        for child in document:
            if child.tag == "Folder":
                n = child.find("name")
                if n is not None and n.text == "图斑边线":
                    folder = child
                    break

        if folder is None:
            folder = SubElement(document, "Folder")
            SubElement(folder, "name").text = "图斑边线"

        style_id = f"poly_{abs(hash((color, self.options['line_width']))) % 1000000}"

        style = SubElement(document, "Style", id=style_id)

        line_style = SubElement(style, "LineStyle")
        SubElement(line_style, "color").text = self.hex_to_kml_color(color)
        SubElement(line_style, "width").text = str(self.options["line_width"])

        poly_style = SubElement(style, "PolyStyle")
        SubElement(poly_style, "fill").text = "0"
        SubElement(poly_style, "outline").text = "1"

        placemark = SubElement(folder, "Placemark")
        SubElement(placemark, "name").text = str(name)
        SubElement(placemark, "styleUrl").text = f"#{style_id}"

        self.add_geometry(placemark, geometry)

    def get_label_position(self, geometry):
        """
        根据界面选择计算标注位置。
        返回：(lon, lat)

        支持：
        1. 自动推荐：质心在面内 -> 质心，否则 -> PointOnSurface
        2. 几何质心：Centroid
        3. 面内点：PointOnSurface
        4. 外接矩形中心：Envelope 中心
        5. 顶点平均中心：外环顶点坐标平均
        """
        mode = self.options.get("label_position", "自动推荐")

        try:
            if mode == "几何质心":
                centroid = geometry.Centroid()
                if centroid:
                    return centroid.GetX(), centroid.GetY()

            elif mode == "面内点":
                point = geometry.PointOnSurface()
                if point:
                    return point.GetX(), point.GetY()

            elif mode == "外接矩形中心":
                env = geometry.GetEnvelope()
                return (
                    (env[0] + env[1]) / 2,
                    (env[2] + env[3]) / 2
                )

            elif mode == "顶点平均中心":
                points = []

                def collect_polygon(poly):
                    if poly is None or poly.GetGeometryCount() == 0:
                        return
                    ring = poly.GetGeometryRef(0)
                    if ring is None:
                        return
                    count = ring.GetPointCount()
                    # 闭合环最后一点通常与第一点重复，因此排除最后重复点
                    usable_count = count
                    if count > 1:
                        x0, y0, _ = ring.GetPoint(0)
                        x1, y1, _ = ring.GetPoint(count - 1)
                        if abs(x0 - x1) < 1e-12 and abs(y0 - y1) < 1e-12:
                            usable_count = count - 1

                    for i in range(usable_count):
                        x, y, _ = ring.GetPoint(i)
                        points.append((x, y))

                geom_type = geometry.GetGeometryName().upper()

                if geom_type == "POLYGON":
                    collect_polygon(geometry)

                elif geom_type == "MULTIPOLYGON":
                    for i in range(geometry.GetGeometryCount()):
                        collect_polygon(geometry.GetGeometryRef(i))

                if points:
                    x = sum(p[0] for p in points) / len(points)
                    y = sum(p[1] for p in points) / len(points)
                    return x, y

            # 默认：自动推荐
            centroid = geometry.Centroid()

            if centroid and geometry.Contains(centroid):
                return centroid.GetX(), centroid.GetY()

            point = geometry.PointOnSurface()
            if point:
                return point.GetX(), point.GetY()

            if centroid:
                return centroid.GetX(), centroid.GetY()

        except Exception:
            pass

        # 最终兜底
        try:
            point = geometry.PointOnSurface()
            if point:
                return point.GetX(), point.GetY()
        except Exception:
            pass

        env = geometry.GetEnvelope()
        return (
            (env[0] + env[1]) / 2,
            (env[2] + env[3]) / 2
        )

    def add_label_to_kml(self, document, lon, lat, label_value):
        folder = None

        for child in document:
            if child.tag == "Folder":
                n = child.find("name")
                if n is not None and n.text == "图斑标注":
                    folder = child
                    break

        if folder is None:
            folder = SubElement(document, "Folder")
            SubElement(folder, "name").text = "图斑标注"

            style = SubElement(document, "Style", id="label_style")

            label_style = SubElement(style, "LabelStyle")
            SubElement(label_style, "color").text = self.hex_to_kml_color(
                self.options["label_color"]
            )
            SubElement(label_style, "scale").text = str(
                self.options["label_size"]
            )

            icon_style = SubElement(style, "IconStyle")

            if self.options["symbol_key"] == "none":
                SubElement(icon_style, "scale").text = "0"
            else:
                SubElement(icon_style, "scale").text = str(
                    self.options["symbol_scale"]
                )
                icon = SubElement(icon_style, "Icon")
                SubElement(icon, "href").text = "icons/symbol.png"

        placemark = SubElement(folder, "Placemark")
        SubElement(placemark, "name").text = str(label_value)
        SubElement(placemark, "styleUrl").text = "#label_style"

        point = SubElement(placemark, "Point")
        SubElement(point, "coordinates").text = f"{lon},{lat},0"

    def create_symbol_png(self, path):
        if self.options["symbol_key"] == "none":
            return None

        pix = render_symbol(
            self.options["symbol_key"],
            self.options["symbol_color"],
            72
        )

        if not pix.save(path, "PNG"):
            raise RuntimeError("生成 KMZ 标注符号失败")

        return path

    def save_kmz(self, kml, output_path):
        rough = tostring(kml, encoding="utf-8")
        parsed = minidom.parseString(rough)
        kml_bytes = parsed.toprettyxml(indent="  ", encoding="utf-8")

        temp_dir = tempfile.mkdtemp(prefix="shp2kmz_")

        try:
            doc_path = os.path.join(temp_dir, "doc.kml")
            with open(doc_path, "wb") as f:
                f.write(kml_bytes)

            symbol_path = None

            if self.options["symbol_key"] != "none":
                icon_dir = os.path.join(temp_dir, "icons")
                os.makedirs(icon_dir, exist_ok=True)
                symbol_path = os.path.join(icon_dir, "symbol.png")
                self.create_symbol_png(symbol_path)

            with zipfile.ZipFile(
                output_path,
                "w",
                zipfile.ZIP_DEFLATED
            ) as kmz:
                kmz.write(doc_path, "doc.kml")

                if symbol_path and os.path.exists(symbol_path):
                    kmz.write(symbol_path, "icons/symbol.png")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def get_label_value(self, feature):
        field_name = self.options["label_field"]
        if not field_name:
            return ""

        value = feature.GetField(field_name)
        return "" if value is None else value

    def get_feature_color(self, feature):
        if self.options["use_field_color"] and self.options["color_field"]:
            value = feature.GetField(self.options["color_field"])
            value = "" if value is None else str(value)

            return self.options["color_mapping"].get(
                value,
                self.options["default_color"]
            )

        return self.options["default_color"]

    def clone_feature_data(self, feature, transform):
        geometry = feature.GetGeometryRef()
        if geometry is None:
            return None

        geom = geometry.Clone()
        if transform:
            geom.Transform(transform)

        return {
            "geometry": geom,
            "label": self.get_label_value(feature),
            "color": self.get_feature_color(feature),
        }

    def convert_single_shp(self, shp_path):
        driver = ogr.GetDriverByName("ESRI Shapefile")
        ds = driver.Open(shp_path, 0)

        if ds is None:
            raise RuntimeError(f"无法打开文件：{shp_path}")

        layer = ds.GetLayer()
        count = layer.GetFeatureCount()
        shp_name = os.path.splitext(os.path.basename(shp_path))[0]

        output_file = os.path.join(
            self.options["output_path"],
            f"{shp_name}_{count}.kmz"
        )

        transform = self.get_transform(layer)
        kml, document = self.create_kml_structure()

        for feature in layer:
            data = self.clone_feature_data(feature, transform)
            if not data:
                continue

            self.add_polygon_to_kml(
                document,
                data["geometry"],
                data["label"],
                data["color"]
            )

            lon, lat = self.get_label_position(data["geometry"])
            self.add_label_to_kml(
                document,
                lon,
                lat,
                data["label"]
            )

        ds = None
        self.save_kmz(kml, output_file)
        return output_file

    def convert_shp_grouped(self, shp_path):
        driver = ogr.GetDriverByName("ESRI Shapefile")
        ds = driver.Open(shp_path, 0)

        if ds is None:
            raise RuntimeError(f"无法打开文件：{shp_path}")

        layer = ds.GetLayer()
        transform = self.get_transform(layer)
        group_field = self.options["group_field"]
        shp_name = os.path.splitext(os.path.basename(shp_path))[0]

        grouped = defaultdict(list)

        for feature in layer:
            value = feature.GetField(group_field)
            value = "未知" if value is None else str(value).strip()
            value = value or "未知"

            data = self.clone_feature_data(feature, transform)
            if data:
                grouped[value].append(data)

        ds = None

        outputs = []

        for group_value, features in grouped.items():
            safe_value = self.sanitize_filename(group_value)
            output_file = os.path.join(
                self.options["output_path"],
                f"{shp_name}_{safe_value}_{len(features)}.kmz"
            )

            kml, document = self.create_kml_structure()

            for data in features:
                self.add_polygon_to_kml(
                    document,
                    data["geometry"],
                    data["label"],
                    data["color"]
                )

                lon, lat = self.get_label_position(data["geometry"])
                self.add_label_to_kml(
                    document,
                    lon,
                    lat,
                    data["label"]
                )

            self.save_kmz(kml, output_file)
            outputs.append(output_file)

        return outputs


# ============================================================
# 转换线程
# ============================================================

class ConvertWorker(QThread):

    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    log_message = pyqtSignal(str)
    finished_result = pyqtSignal(int, int, int)
    fatal_error = pyqtSignal(str)

    def __init__(self, shp_files, options, parent=None):
        super().__init__(parent)
        self.shp_files = shp_files
        self.options = options

    def run(self):
        try:
            core = ShpToKmzCore(
                self.options,
                logger=self.log_message.emit
            )

            total = len(self.shp_files)
            success = 0
            failed = 0
            kmz_count = 0

            self.log_message.emit("=" * 56)

            if self.options["use_group_export"]:
                self.log_message.emit(
                    f"开始批量转换（分组导出），共 {total} 个 SHP"
                )
                self.log_message.emit(
                    f"分组字段：{self.options['group_field']}"
                )
            else:
                self.log_message.emit(
                    f"开始批量转换，共 {total} 个 SHP"
                )

            self.log_message.emit("=" * 56)

            for i, shp_file in enumerate(self.shp_files, 1):
                self.status_changed.emit(
                    f"正在处理：{os.path.basename(shp_file)}"
                )
                self.progress_changed.emit(
                    int((i - 1) / total * 100)
                )
                self.log_message.emit(
                    f"[{i}/{total}] {os.path.basename(shp_file)}"
                )

                try:
                    if self.options["use_group_export"]:
                        outputs = core.convert_shp_grouped(shp_file)
                        success += 1
                        kmz_count += len(outputs)

                        self.log_message.emit(
                            f"  ✓ 成功生成 {len(outputs)} 个 KMZ"
                        )

                        for path in outputs:
                            self.log_message.emit(
                                f"    - {os.path.basename(path)}"
                            )

                    else:
                        output = core.convert_single_shp(shp_file)
                        success += 1
                        kmz_count += 1
                        self.log_message.emit(
                            f"  ✓ {os.path.basename(output)}"
                        )

                except Exception as e:
                    failed += 1
                    self.log_message.emit(
                        f"  ✗ {e}"
                    )

            self.progress_changed.emit(100)
            self.status_changed.emit("转换完成")

            self.log_message.emit("=" * 56)
            self.log_message.emit(
                f"完成：{success} 成功，{failed} 失败，共生成 {kmz_count} 个 KMZ"
            )
            self.log_message.emit("=" * 56)

            self.finished_result.emit(
                success,
                failed,
                kmz_count
            )

        except Exception as e:
            self.fatal_error.emit(str(e))


# ============================================================
# 主窗口
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1300, 980)
        self.setMinimumSize(1120, 840)

        if os.path.exists(application_icon()):
            self.setWindowIcon(QIcon(application_icon()))

        # 默认参数，延续 V2.4
        self.default_color = "#FF0000"
        self.label_color = "#FFFFFF"
        self.symbol_color = "#E53935"
        self.symbol_key = "none"

        self.color_mapping = {}
        self.available_fields = []
        self.worker = None

        self.build_ui()
        self.apply_theme()

    # --------------------------------------------------------
    # 主题
    # --------------------------------------------------------

    def apply_theme(self):
        app_font = QFont("Microsoft YaHei", 12)
        QApplication.instance().setFont(app_font)

        self.setStyleSheet("""
            QMainWindow {
                background:#F3F6FA;
            }

            QWidget {
                color:#273444;
            }

            QLabel {
                font-size:15px;
            }

            QLabel#pageTitle {
                font-size:21px;
                font-weight:600;
                color:#173B63;
            }

            QLabel#pageSubtitle {
                font-size:13px;
                color:#7A8797;
            }

            QLabel#sectionHint {
                font-size:14px;
                color:#7A8797;
            }

            QLabel#statusReady {
                font-size:14px;
                font-weight:600;
                color:#16803A;
            }

            QGroupBox {
                background:#FFFFFF;
                border:1px solid #DCE3EC;
                border-radius:9px;
                margin-top:12px;
                padding-top:8px;
                font-size:15px;
                font-weight:600;
                color:#234E78;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left:14px;
                padding:0 7px;
                background:#FFFFFF;
            }

            QLineEdit, QComboBox, QDoubleSpinBox {
                min-height:38px;
                max-height:40px;
                border:1px solid #C8D2DE;
                border-radius:6px;
                background:#FFFFFF;
                padding:0 8px;
                font-size:15px;
            }

            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border:1px solid #4A86C5;
            }

            QComboBox::drop-down {
                width:26px;
                border:none;
            }

            QPushButton {
                min-height:38px;
                max-height:42px;
                border:1px solid #C2CCD8;
                border-radius:6px;
                background:#F8FAFC;
                padding:2px 12px;
                font-size:15px;
            }

            QPushButton:hover {
                background:#EEF5FC;
                border-color:#83A9D1;
            }

            QPushButton:pressed {
                background:#DFECF8;
            }

            QPushButton:disabled {
                color:#A4ABB5;
                background:#F2F4F7;
                border-color:#E1E5EA;
            }

            QPushButton#primaryButton {
                color:#FFFFFF;
                font-weight:600;
                font-size:14px;
                background:#2F6FED;
                border:1px solid #2F6FED;
                border-radius:7px;
                min-height:46px;
            }

            QPushButton#primaryButton:hover {
                background:#255FD1;
            }

            QPushButton#secondaryButton {
                background:#FFFFFF;
            }

            QCheckBox {
                spacing:7px;
                font-size:14px;
            }

            QCheckBox::indicator {
                width:19px;
                height:19px;
            }

            QProgressBar {
                min-height:18px;
                max-height:18px;
                border:1px solid #D8E0EA;
                border-radius:5px;
                background:#FFFFFF;
                text-align:center;
            }

            QProgressBar::chunk {
                background:#4A86C5;
                border-radius:4px;
            }

            QPlainTextEdit {
                background:#FBFCFE;
                border:1px solid #DCE3EC;
                border-radius:7px;
                padding:7px;
                font-family:Consolas;
                font-size:14px;
            }

            QListWidget {
                background:#FFFFFF;
                border:1px solid #DCE3EC;
                border-radius:7px;
                padding:7px;
            }

            QListWidget::item {
                border:1px solid transparent;
                border-radius:7px;
                padding:5px;
            }

            QListWidget::item:selected {
                background:#E9F2FC;
                border:1px solid #8AB2DD;
                color:#194A78;
            }

            QScrollArea {
                border:none;
                background:transparent;
            }
        """)

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def build_ui(self):
        """
        响应式主界面。

        核心原则：
        1. 顶部标题、底部信息固定；
        2. “数据与输出 + 参数设置 + 运行”放入滚动区域；
        3. 参数区域不足时出现滚动条，而不是压缩控件；
        4. 日志区独立保留最小高度；
        5. 显示样式 / 字段处理保持左右双栏。
        """
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(18, 8, 18, 12)
        root.setSpacing(10)

        # ----------------------------------------------------
        # 顶部标题

        # ----------------------------------------------------
        # 上下可调区域：
        # 上部 = 参数滚动区
        # 下部 = 日志区
        # ----------------------------------------------------
        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.setChildrenCollapsible(False)
        vertical_splitter.setHandleWidth(5)

        # ==================== 参数滚动区 ====================
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        settings_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 4, 2)
        settings_layout.setSpacing(10)

        # 数据与输出
        path_group = self.build_path_group()
        path_group.setMinimumHeight(145)
        path_group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )
        settings_layout.addWidget(path_group)

        # 中部双栏
        middle = QSplitter(Qt.Horizontal)
        middle.setChildrenCollapsible(False)
        middle.setHandleWidth(6)
        middle.setMinimumHeight(470)
        middle.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        style_panel = self.build_style_group()
        field_panel = self.build_field_group()

        style_panel.setMinimumHeight(455)
        field_panel.setMinimumHeight(410)

        style_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        field_panel.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        middle.addWidget(style_panel)
        middle.addWidget(field_panel)
        middle.setStretchFactor(0, 1)
        middle.setStretchFactor(1, 1)
        middle.setSizes([570, 530])

        settings_layout.addWidget(middle)

        # 运行区
        run_group = self.build_run_group()
        run_group.setMinimumHeight(115)
        run_group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )
        settings_layout.addWidget(run_group)

        settings_layout.addStretch(0)

        settings_scroll.setWidget(settings_widget)
        settings_scroll.setMinimumHeight(500)

        vertical_splitter.addWidget(settings_scroll)

        # ==================== 日志区 ====================
        log_group = self.build_log_group()
        log_group.setMinimumHeight(220)
        log_group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        vertical_splitter.addWidget(log_group)

        vertical_splitter.setStretchFactor(0, 3)
        vertical_splitter.setStretchFactor(1, 2)
        vertical_splitter.setSizes([620, 280])

        root.addWidget(vertical_splitter, 1)

        # ----------------------------------------------------
        # 底部信息
        # ----------------------------------------------------
        footer = QHBoxLayout()

        copyright_label = QLabel(
            f"{COPYRIGHT_TEXT}  ·  微信公众号：测绘地信  ·  知识星球：测绘地理信息共享中心"
        )
        copyright_label.setStyleSheet(
            "color:#7A8797;font-size:11px;"
        )

        footer.addWidget(copyright_label)
        footer.addStretch()

        support = QLabel(
            f"技术支持：{SUPPORT_EMAIL}"
        )
        support.setStyleSheet(
            "color:#7A8797;font-size:11px;"
        )
        footer.addWidget(support)

        root.addLayout(footer)

    def build_path_group(self):
        group = QGroupBox("数据与输出")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(10)
        layout.setContentsMargins(14, 15, 14, 12)
        layout.setColumnStretch(1, 1)
        layout.setRowMinimumHeight(0, 42)
        layout.setRowMinimumHeight(1, 42)

        input_label = QLabel("输入数据")
        output_label = QLabel("输出目录")
        input_label.setMinimumWidth(62)
        output_label.setMinimumWidth(62)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText(
            "选择 SHP 文件夹，或选择一个/多个 SHP 文件"
        )

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("选择 KMZ 输出目录")

        btn_folder = QPushButton("选择文件夹")
        btn_files = QPushButton("选择文件")
        btn_output = QPushButton("浏览...")

        btn_folder.clicked.connect(self.select_folder)
        btn_files.clicked.connect(self.select_files)
        btn_output.clicked.connect(self.select_output)

        layout.addWidget(input_label, 0, 0)
        layout.addWidget(self.input_edit, 0, 1)
        layout.addWidget(btn_folder, 0, 2)
        layout.addWidget(btn_files, 0, 3)

        layout.addWidget(output_label, 1, 0)
        layout.addWidget(self.output_edit, 1, 1, 1, 2)
        layout.addWidget(btn_output, 1, 3)

        return group

    def build_style_group(self):
        group = QGroupBox("显示样式")
        layout = QGridLayout(group)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(9)

        for row in range(10):
            layout.setRowMinimumHeight(row, 38)

        # 边线
        boundary_title = QLabel("图斑边线")
        boundary_title.setStyleSheet("font-weight:600;color:#334155;")
        layout.addWidget(boundary_title, 0, 0, 1, 4)

        layout.addWidget(QLabel("线宽"), 1, 0)

        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.1, 50.0)
        self.line_width_spin.setDecimals(1)
        self.line_width_spin.setSingleStep(0.5)
        self.line_width_spin.setValue(2.0)
        layout.addWidget(self.line_width_spin, 1, 1)

        layout.addWidget(QLabel("颜色"), 1, 2)

        self.border_color_btn = QPushButton()
        self.border_color_btn.setFixedWidth(72)
        self.border_color_btn.setStyleSheet(
            make_color_button_style(self.default_color)
        )
        self.border_color_btn.clicked.connect(self.choose_border_color)
        layout.addWidget(self.border_color_btn, 1, 3)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#E3E8EF;")
        layout.addWidget(line, 2, 0, 1, 4)

        # 标注
        label_title = QLabel("图斑标注")
        label_title.setStyleSheet("font-weight:600;color:#334155;")
        layout.addWidget(label_title, 3, 0, 1, 4)

        layout.addWidget(QLabel("标注字段"), 4, 0)

        self.label_field_combo = QComboBox()
        self.label_field_combo.setMinimumWidth(140)
        layout.addWidget(self.label_field_combo, 4, 1, 1, 2)

        btn_load_label = QPushButton("加载字段")
        btn_load_label.clicked.connect(self.load_fields_for_label)
        layout.addWidget(btn_load_label, 4, 3)

        layout.addWidget(QLabel("标注位置"), 5, 0)

        self.label_position_combo = QComboBox()
        self.label_position_combo.addItems([
            "自动推荐",
            "几何质心",
            "面内点",
            "外接矩形中心",
            "顶点平均中心"
        ])
        self.label_position_combo.setCurrentText("自动推荐")
        layout.addWidget(self.label_position_combo, 5, 1, 1, 3)

        layout.addWidget(QLabel("字体大小"), 6, 0)

        self.label_size_spin = QDoubleSpinBox()
        self.label_size_spin.setRange(0.1, 20.0)
        self.label_size_spin.setDecimals(1)
        self.label_size_spin.setValue(1.0)
        layout.addWidget(self.label_size_spin, 6, 1)

        layout.addWidget(QLabel("字体颜色"), 6, 2)

        self.label_color_btn = QPushButton()
        self.label_color_btn.setFixedWidth(72)
        self.label_color_btn.setStyleSheet(
            make_color_button_style(self.label_color)
        )
        self.label_color_btn.clicked.connect(self.choose_label_color)
        layout.addWidget(self.label_color_btn, 6, 3)

        layout.addWidget(QLabel("标注符号"), 7, 0)

        symbol_box = QHBoxLayout()
        symbol_box.setSpacing(8)

        self.symbol_preview = QLabel()
        self.symbol_preview.setFixedSize(42, 42)
        self.symbol_preview.setAlignment(Qt.AlignCenter)
        self.symbol_preview.setStyleSheet(
            "background:#F8FAFC;border:1px solid #D8E0EA;"
            "border-radius:6px;"
        )
        self.refresh_symbol_preview()

        self.symbol_name = QLabel("无")
        self.symbol_name.setMinimumWidth(52)

        btn_symbol = QPushButton("符号库...")
        btn_symbol.clicked.connect(self.choose_symbol)

        symbol_box.addWidget(self.symbol_preview)
        symbol_box.addWidget(self.symbol_name)
        symbol_box.addWidget(btn_symbol)
        symbol_box.addStretch()

        layout.addLayout(symbol_box, 7, 1, 1, 3)

        layout.addWidget(QLabel("符号大小"), 8, 0)

        self.symbol_scale_spin = QDoubleSpinBox()
        self.symbol_scale_spin.setRange(0.1, 20.0)
        self.symbol_scale_spin.setDecimals(1)
        self.symbol_scale_spin.setValue(1.0)
        layout.addWidget(self.symbol_scale_spin, 8, 1)

        layout.addWidget(QLabel("符号颜色"), 8, 2)

        self.symbol_color_btn = QPushButton()
        self.symbol_color_btn.setFixedWidth(72)
        self.symbol_color_btn.setStyleSheet(
            make_color_button_style(self.symbol_color)
        )
        self.symbol_color_btn.clicked.connect(self.choose_symbol_color)
        layout.addWidget(self.symbol_color_btn, 8, 3)

        hint = QLabel(
            "标注位置支持自动推荐、几何质心、面内点、外接矩形中心和顶点平均中心。"
        )
        hint.setObjectName("sectionHint")
        hint.setWordWrap(True)
        layout.addWidget(hint, 9, 0, 1, 4)

        layout.setColumnMinimumWidth(0, 72)
        layout.setColumnMinimumWidth(2, 72)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        return group

    def build_field_group(self):
        group = QGroupBox("字段处理")
        layout = QGridLayout(group)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(9)

        for row in range(9):
            layout.setRowMinimumHeight(row, 38)

        # 字段着色
        color_title = QLabel("按字段着色")
        color_title.setStyleSheet("font-weight:600;color:#334155;")
        layout.addWidget(color_title, 0, 0, 1, 4)

        self.use_field_color_cb = QCheckBox("启用字段分组着色")
        self.use_field_color_cb.toggled.connect(self.toggle_field_color)
        layout.addWidget(self.use_field_color_cb, 1, 0, 1, 4)

        layout.addWidget(QLabel("着色字段"), 2, 0)

        self.color_field_combo = QComboBox()
        self.color_field_combo.setEnabled(False)
        layout.addWidget(self.color_field_combo, 2, 1, 1, 2)

        self.color_load_btn = QPushButton("加载字段")
        self.color_load_btn.setEnabled(False)
        self.color_load_btn.clicked.connect(self.load_fields_for_color)
        layout.addWidget(self.color_load_btn, 2, 3)

        self.color_mapping_btn = QPushButton("设置字段值颜色...")
        self.color_mapping_btn.setEnabled(False)
        self.color_mapping_btn.clicked.connect(self.setup_color_mapping)
        layout.addWidget(self.color_mapping_btn, 3, 1, 1, 3)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#E3E8EF;")
        layout.addWidget(line, 4, 0, 1, 4)

        # 分组导出
        export_title = QLabel("按字段分组导出")
        export_title.setStyleSheet("font-weight:600;color:#334155;")
        layout.addWidget(export_title, 5, 0, 1, 4)

        self.use_group_export_cb = QCheckBox("启用分组导出")
        self.use_group_export_cb.toggled.connect(self.toggle_group_export)
        layout.addWidget(self.use_group_export_cb, 6, 0, 1, 4)

        layout.addWidget(QLabel("分组字段"), 7, 0)

        self.group_field_combo = QComboBox()
        self.group_field_combo.setEnabled(False)
        layout.addWidget(self.group_field_combo, 7, 1, 1, 2)

        self.group_load_btn = QPushButton("加载字段")
        self.group_load_btn.setEnabled(False)
        self.group_load_btn.clicked.connect(self.load_fields_for_group)
        layout.addWidget(self.group_load_btn, 7, 3)

        hint = QLabel(
            "启用后按字段值分别生成 KMZ，命名：原SHP名_分组值_数量.kmz"
        )
        hint.setObjectName("sectionHint")
        hint.setWordWrap(True)
        layout.addWidget(hint, 8, 0, 1, 4)

        layout.setColumnMinimumWidth(0, 78)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)

        return group

    def build_run_group(self):
        group = QGroupBox("运行")
        layout = QGridLayout(group)
        layout.setContentsMargins(14, 15, 14, 12)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(7)
        layout.setRowMinimumHeight(0, 40)
        layout.setRowMinimumHeight(1, 32)

        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setObjectName("primaryButton")
        self.convert_btn.setMinimumWidth(210)
        self.convert_btn.clicked.connect(self.start_conversion)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusReady")
        self.status_label.setMinimumWidth(70)

        layout.addWidget(self.convert_btn, 0, 0, 2, 1)
        layout.addWidget(self.progress_bar, 0, 1)
        layout.addWidget(self.status_label, 1, 1)

        layout.setColumnStretch(1, 1)

        return group

    def build_log_group(self):
        group = QGroupBox("处理日志")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        self.log_edit = QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("转换过程和错误信息将在这里显示...")
        self.log_edit.setMinimumHeight(150)
        layout.addWidget(self.log_edit, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.log_edit.clear)

        help_btn = QPushButton("帮助")
        help_btn.clicked.connect(self.show_help)

        exit_btn = QPushButton("退出")
        exit_btn.clicked.connect(self.close)

        buttons.addWidget(clear_btn)
        buttons.addWidget(help_btn)
        buttons.addWidget(exit_btn)

        layout.addLayout(buttons)

        return group

    # --------------------------------------------------------
    # 颜色与符号
    # --------------------------------------------------------

    def choose_border_color(self):
        c = QColorDialog.getColor(
            QColor(self.default_color),
            self,
            "选择边线颜色"
        )
        if c.isValid():
            self.default_color = c.name().upper()
            self.border_color_btn.setStyleSheet(
                make_color_button_style(self.default_color)
            )
            self.log(f"边线颜色：{self.default_color}")

    def choose_label_color(self):
        c = QColorDialog.getColor(
            QColor(self.label_color),
            self,
            "选择标注字体颜色"
        )
        if c.isValid():
            self.label_color = c.name().upper()
            self.label_color_btn.setStyleSheet(
                make_color_button_style(self.label_color)
            )
            self.log(f"字体颜色：{self.label_color}")

    def choose_symbol_color(self):
        c = QColorDialog.getColor(
            QColor(self.symbol_color),
            self,
            "选择标注符号颜色"
        )
        if c.isValid():
            self.symbol_color = c.name().upper()
            self.symbol_color_btn.setStyleSheet(
                make_color_button_style(self.symbol_color)
            )
            self.refresh_symbol_preview()
            self.log(f"符号颜色：{self.symbol_color}")

    def choose_symbol(self):
        dlg = SymbolLibraryDialog(
            self.symbol_key,
            self.symbol_color,
            self
        )

        if dlg.exec_() == QDialog.Accepted:
            self.symbol_key = dlg.selected_key

            name = next(
                (
                    n for n, key, _ in SYMBOL_LIBRARY
                    if key == self.symbol_key
                ),
                "无"
            )

            self.symbol_name.setText(name)
            self.refresh_symbol_preview()
            self.log(f"标注符号：{name}")

    def refresh_symbol_preview(self):
        if hasattr(self, "symbol_preview"):
            self.symbol_preview.setPixmap(
                render_symbol(
                    self.symbol_key,
                    self.symbol_color,
                    36
                )
            )

    # --------------------------------------------------------
    # 文件选择
    # --------------------------------------------------------

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择输入文件夹"
        )
        if folder:
            self.input_edit.setText(folder)
            self.log(f"输入文件夹：{folder}")

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择 SHP 文件",
            "",
            "Shapefile (*.shp)"
        )

        if files:
            self.input_edit.setText(";".join(files))
            self.log(f"已选择 {len(files)} 个 SHP 文件")

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录"
        )
        if folder:
            self.output_edit.setText(folder)
            self.log(f"输出目录：{folder}")

    def get_shp_files(self):
        path = self.input_edit.text().strip()

        if not path:
            return []

        if os.path.isdir(path):
            return sorted(
                glob.glob(os.path.join(path, "*.shp"))
            )

        if ";" in path:
            return [
                p for p in path.split(";")
                if p and os.path.isfile(p)
            ]

        if os.path.isfile(path):
            return [path]

        return []

    # --------------------------------------------------------
    # 字段
    # --------------------------------------------------------

    def read_fields(self):
        shp_files = self.get_shp_files()

        if not shp_files:
            QMessageBox.warning(
                self,
                "提示",
                "请先选择 SHP 文件或文件夹。"
            )
            return None

        try:
            driver = ogr.GetDriverByName("ESRI Shapefile")
            ds = driver.Open(shp_files[0], 0)

            if ds is None:
                raise RuntimeError("无法打开 SHP 文件")

            layer = ds.GetLayer()
            defn = layer.GetLayerDefn()

            fields = [
                defn.GetFieldDefn(i).GetName()
                for i in range(defn.GetFieldCount())
            ]

            ds = None
            self.available_fields = fields
            return fields

        except Exception as e:
            QMessageBox.critical(
                self,
                "字段读取失败",
                str(e)
            )
            return None

    @staticmethod
    def fill_combo(combo, fields, preferred=None):
        current = combo.currentText()

        combo.blockSignals(True)
        combo.clear()
        combo.addItems(fields)

        if preferred and preferred in fields:
            combo.setCurrentText(preferred)
        elif current in fields:
            combo.setCurrentText(current)
        elif fields:
            combo.setCurrentIndex(0)

        combo.blockSignals(False)

    def sync_all_field_combos(
        self,
        fields,
        preferred_group=None,
        preferred_label=None
    ):
        self.fill_combo(
            self.color_field_combo,
            fields
        )
        self.fill_combo(
            self.group_field_combo,
            fields,
            preferred_group
        )
        self.fill_combo(
            self.label_field_combo,
            fields,
            preferred_label
        )

        self.log(
            f"已加载 {len(fields)} 个字段：{', '.join(fields)}"
        )

    def load_fields_for_color(self):
        fields = self.read_fields()
        if fields is None:
            return

        label_pref = "jcbh" if "jcbh" in fields else None
        self.sync_all_field_combos(
            fields,
            preferred_label=label_pref
        )

    def load_fields_for_label(self):
        fields = self.read_fields()
        if fields is None:
            return

        label_pref = "jcbh" if "jcbh" in fields else None
        self.sync_all_field_combos(
            fields,
            preferred_label=label_pref
        )

    def load_fields_for_group(self):
        fields = self.read_fields()
        if fields is None:
            return

        preferred_group = None
        for f in [
            "xzmc", "xzqmc", "xzqdm",
            "xjmc", "xjdm", "dkmc"
        ]:
            if f in fields:
                preferred_group = f
                break

        label_pref = "jcbh" if "jcbh" in fields else None

        self.sync_all_field_combos(
            fields,
            preferred_group=preferred_group,
            preferred_label=label_pref
        )

    def toggle_field_color(self, checked):
        self.color_field_combo.setEnabled(checked)
        self.color_load_btn.setEnabled(checked)
        self.color_mapping_btn.setEnabled(checked)

    def toggle_group_export(self, checked):
        self.group_field_combo.setEnabled(checked)
        self.group_load_btn.setEnabled(checked)

    def setup_color_mapping(self):
        field_name = self.color_field_combo.currentText().strip()

        if not field_name:
            QMessageBox.warning(
                self,
                "提示",
                "请先加载并选择着色字段。"
            )
            return

        shp_files = self.get_shp_files()
        if not shp_files:
            return

        values = set()
        driver = ogr.GetDriverByName("ESRI Shapefile")

        try:
            # 延续 V2.4：最多读取前 5 个 SHP
            for shp in shp_files[:5]:
                ds = driver.Open(shp, 0)
                if ds is None:
                    continue

                layer = ds.GetLayer()

                for feature in layer:
                    value = feature.GetField(field_name)
                    if value is not None:
                        values.add(str(value))

                ds = None

            if not values:
                QMessageBox.information(
                    self,
                    "提示",
                    "该字段未读取到有效字段值。"
                )
                return

            dlg = ColorMappingDialog(
                field_name,
                values,
                self.color_mapping,
                self
            )

            if dlg.exec_() == QDialog.Accepted:
                self.color_mapping = dlg.mapping
                self.log(
                    f"已设置字段“{field_name}”颜色映射："
                    f"{len(self.color_mapping)} 项"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "颜色映射失败",
                str(e)
            )

    # --------------------------------------------------------
    # 转换
    # --------------------------------------------------------

    def collect_options(self):
        return {
            "output_path": self.output_edit.text().strip(),
            "line_width": self.line_width_spin.value(),
            "default_color": self.default_color,

            "use_field_color": self.use_field_color_cb.isChecked(),
            "color_field": self.color_field_combo.currentText().strip(),
            "color_mapping": dict(self.color_mapping),

            "use_group_export": self.use_group_export_cb.isChecked(),
            "group_field": self.group_field_combo.currentText().strip(),

            "label_field": self.label_field_combo.currentText().strip(),
            "label_position": self.label_position_combo.currentText().strip(),
            "label_size": self.label_size_spin.value(),
            "label_color": self.label_color,

            "symbol_key": self.symbol_key,
            "symbol_color": self.symbol_color,
            "symbol_scale": self.symbol_scale_spin.value(),
        }

    def validate_before_run(self):
        shp_files = self.get_shp_files()

        if not shp_files:
            QMessageBox.warning(
                self,
                "无法开始",
                "未找到可转换的 SHP 文件。"
            )
            return None

        output = self.output_edit.text().strip()

        if not output:
            QMessageBox.warning(
                self,
                "无法开始",
                "请选择输出目录。"
            )
            return None

        if not os.path.isdir(output):
            QMessageBox.warning(
                self,
                "无法开始",
                "输出目录不存在。"
            )
            return None

        if (
            self.use_field_color_cb.isChecked()
            and not self.color_field_combo.currentText().strip()
        ):
            QMessageBox.warning(
                self,
                "无法开始",
                "已启用字段分组着色，但尚未选择着色字段。"
            )
            return None

        if (
            self.use_group_export_cb.isChecked()
            and not self.group_field_combo.currentText().strip()
        ):
            QMessageBox.warning(
                self,
                "无法开始",
                "已启用分组导出，但尚未选择分组字段。"
            )
            return None

        return shp_files

    def start_conversion(self):
        shp_files = self.validate_before_run()

        if shp_files is None:
            return

        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.set_status("准备转换...", "blue")

        options = self.collect_options()

        self.worker = ConvertWorker(
            shp_files,
            options,
            self
        )

        self.worker.progress_changed.connect(
            self.progress_bar.setValue
        )
        self.worker.status_changed.connect(
            lambda text: self.set_status(text, "blue")
        )
        self.worker.log_message.connect(self.log)
        self.worker.finished_result.connect(self.on_finished)
        self.worker.fatal_error.connect(self.on_fatal_error)

        self.worker.start()

    def on_finished(self, success, failed, kmz_count):
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.set_status("转换完成", "green")

        QMessageBox.information(
            self,
            "转换完成",
            f"SHP 文件：{success} 成功 / {failed} 失败\n"
            f"生成 KMZ：{kmz_count} 个"
        )

    def on_fatal_error(self, message):
        self.convert_btn.setEnabled(True)
        self.set_status("转换失败", "red")

        QMessageBox.critical(
            self,
            "转换失败",
            message
        )

    def set_status(self, text, color):
        color_map = {
            "green": "#16803A",
            "blue": "#2563EB",
            "red": "#D32F2F",
        }

        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"font-size:13px;font-weight:600;"
            f"color:{color_map.get(color, '#334155')};"
        )

    # --------------------------------------------------------
    # 日志与帮助
    # --------------------------------------------------------

    def log(self, message):
        self.log_edit.appendPlainText(str(message))
        sb = self.log_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    def show_help(self):
        text = f"""【{APP_NAME} {APP_VERSION}】

一、数据与输出
支持选择 SHP 文件夹，也支持一次选择多个 SHP 文件；结果输出为 KMZ。

二、显示样式
可设置图斑边线宽度和颜色；可设置标注字段、字号、字体颜色、符号、符号颜色和符号大小。

三、字段处理
1. 字段分组着色：按指定字段值为图斑边线设置不同颜色。
2. 分组导出：按字段值分别生成多个 KMZ。
3. 分组输出命名：原SHP名_分组值_数量.kmz。

四、标注位置
支持以下五种方式：
1. 自动推荐：质心在图斑内时使用质心，否则自动使用面内点。
2. 几何质心：直接采用几何质心。
3. 面内点：采用 PointOnSurface，保证点位于图斑内部。
4. 外接矩形中心：采用图斑外接矩形中心。
5. 顶点平均中心：对图斑外环顶点坐标求平均。

五、符号
内置符号采用本工具动态绘制，不依赖在线图标；选中的符号会作为 PNG 一并写入 KMZ，可离线使用。

六、程序图标
自动读取程序或 EXE 当前目录下的 icon.png。

版权：{COPYRIGHT_TEXT}
技术支持：{SUPPORT_EMAIL}
"""

        QMessageBox.information(
            self,
            "使用说明",
            text
        )


# ============================================================
# 启动
# ============================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(f"SHP2KMZ Tool {APP_VERSION}")

    if os.path.exists(application_icon()):
        app.setWindowIcon(QIcon(application_icon()))

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
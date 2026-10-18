"""Generate the dual-mode architecture SVG with the Python standard library.

Run from the repository root: python docs/assets/generate_architecture.py
The committed PNG is a raster export for consistent README display.
"""

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent


INK = "#172B3A"
MUTED = "#5A6F7C"
BLUE = "#315ED4"
TEAL = "#087C6F"


def node(parent, tag, **attrs):
    """Normalize Python-friendly names to SVG attributes."""
    return SubElement(parent, tag, {key.replace("_", "-"): str(value) for key, value in attrs.items()})


def text(parent, x, y, value, size=24, color=INK, weight=400):
    """Position one baseline so all cards share consistent typography."""
    element = node(parent, "text", x=x, y=y, fill=color, font_size=size, font_weight=weight)
    element.text = value


def box(parent, x, y, width, height, fill="#FFFFFF", stroke="#D4E0E7", radius=18):
    """Draw a flat system boundary or module card."""
    node(parent, "rect", x=x, y=y, width=width, height=height, rx=radius, fill=fill, stroke=stroke, stroke_width=1.5)


def arrow(parent, path, dashed=False):
    """Use orthogonal, directional lines for module relationships."""
    attrs = {"d": path, "fill": "none", "stroke": "#8CA1AF", "stroke_width": 2.5, "marker_end": "url(#arrow)", "stroke_linejoin": "round"}
    if dashed:
        attrs["stroke_dasharray"] = "7 6"
    node(parent, "path", **attrs)


def card(parent, x, y, width, height, label, title, subtitle, accent=BLUE):
    """Use three text levels for labels, components and concrete behavior."""
    box(parent, x, y, width, height)
    text(parent, x + 26, y + 35, label, 17, accent, 700)
    text(parent, x + 26, y + 77, title, 29, INK, 700)
    text(parent, x + 26, y + 113, subtitle, 22, MUTED)


def build_svg():
    """Show shared browser capabilities and separate local/server storage paths."""
    svg = Element("svg", {"xmlns": "http://www.w3.org/2000/svg", "width": "1600", "height": "1230", "viewBox": "0 0 1600 1230", "font-family": "Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif"})
    node(svg, "title").text = "刷题通：本地版与部署版系统架构"
    node(svg, "desc").text = "两份页面分别提供浏览器文档解析、预览纠错与练习考试。本地版使用 localStorage；部署版通过 Flask API、内存 Token 和每用户 JSON 目录保存数据。Docker Compose 挂载页面与数据目录。"
    defs = node(svg, "defs")
    marker = node(defs, "marker", id="arrow", markerWidth=9, markerHeight=9, refX=8, refY=4.5, orient="auto", markerUnits="userSpaceOnUse")
    node(marker, "path", d="M 0 0 L 9 4.5 L 0 9 z", fill="#8CA1AF")
    box(svg, 0, 0, 1600, 1230, "#F7F9FC", "#F7F9FC", 0)
    box(svg, 64, 54, 7, 105, BLUE, BLUE, 2)
    text(svg, 94, 76, "SHUATI / TWO MODES, ONE STUDY WORKFLOW", 18, BLUE, 700)
    text(svg, 89, 145, "刷题通", 62, INK, 700)
    text(svg, 325, 141, "从文档到题库，从练习到复习", 31, MUTED)
    text(svg, 94, 187, "原生 JavaScript 页面  ·  Flask 服务  ·  无数据库  ·  无前端打包", 24, MUTED)

    card(svg, 64, 232, 700, 140, "BROWSER / IMPORT", "文档解析与题目标准化", "DOCX · XLSX / XLS · TXT · 文本型 PDF")
    card(svg, 836, 232, 700, 140, "BROWSER / REVIEW", "预览纠错 → 练习 / 模拟考试", "五种题型 · 重复检查 · 错题重练 · 答题卡")
    arrow(svg, "M 764 302 H 836")
    text(svg, 64, 412, "下方两份页面分别实现上述能力；它们使用不同的数据存储入口。", 21, MUTED)

    box(svg, 64, 452, 700, 636, "#EDF2FF", "#C7D6F7", 24)
    box(svg, 836, 452, 700, 636, "#EAF6F2", "#BEDFD3", 24)
    text(svg, 94, 498, "MODE A  /  本地使用", 24, BLUE, 700)
    text(svg, 866, 498, "MODE B  /  服务端部署", 24, TEAL, 700)

    card(svg, 94, 536, 640, 140, "ENTRY / NO LOGIN", "index.html", "直接打开浏览器页面，无需后端服务")
    card(svg, 866, 536, 640, 140, "ENTRY / ACCOUNT LOGIN", "static/index.html", "Flask 提供页面，fetch 调用同源 /api", TEAL)
    arrow(svg, "M 414 676 V 782")
    text(svg, 436, 740, "浏览器读写", 20, MUTED)
    arrow(svg, "M 1186 676 V 730")

    card(svg, 94, 782, 640, 166, "PERSISTENCE / DEVICE LOCAL", "localStorage", "题库 · 题目 · 答题记录 · 普通练习进度")
    text(svg, 120, 925, "存储在当前浏览器及当前来源", 21, MUTED)

    box(svg, 866, 730, 640, 140, "#153D3A", "#153D3A")
    text(svg, 892, 765, "API / PYTHON + FLASK", 17, "#A9DAD0", 700)
    text(svg, 892, 807, "认证 · 用户管理 · 题库与进度", 29, "#FFFFFF", 700)
    text(svg, 892, 843, "Bearer Token · 管理员 / 普通用户", 22, "#D0E7E0")
    node(svg, "path", d="M 1186 870 V 900 H 1080 M 1186 900 H 1395", stroke="#8CA1AF", stroke_width=2.5, fill="none")
    arrow(svg, "M 1080 900 V 924")
    arrow(svg, "M 1395 900 V 924", True)
    box(svg, 866, 924, 428, 132)
    text(svg, 890, 959, "PERSISTENCE / SERVER", 16, TEAL, 700)
    text(svg, 890, 1000, "每用户 JSON 目录", 28, INK, 700)
    text(svg, 890, 1034, "账号 · 题库 · 记录 · 练习进度", 21, MUTED)
    box(svg, 1318, 924, 188, 132)
    text(svg, 1340, 959, "SESSION", 16, TEAL, 700)
    text(svg, 1340, 1000, "内存 Token", 24, INK, 700)
    text(svg, 1340, 1034, "服务重启失效", 19, MUTED)

    text(svg, 94, 1007, "题库数据不自动跨设备同步", 24, BLUE, 700)
    text(svg, 94, 1048, "与部署版存储相互独立，没有自动迁移", 21, MUTED)
    node(svg, "path", d="M 64 1130 H 1536", stroke="#D4E0E7", stroke_width=1.5)
    text(svg, 64, 1174, "DEPLOYMENT", 17, TEAL, 700)
    text(svg, 278, 1174, "Docker Compose  :4000", 25, INK, 700)
    text(svg, 780, 1174, "./static → /app/static", 23, MUTED)
    text(svg, 1230, 1174, "./data → /data", 23, MUTED)
    text(svg, 64, 1211, "JSON 存储适合受控单实例使用；所有解析与判题逻辑在浏览器运行。", 19, MUTED)
    return svg


def main():
    """Keep the editable vector alongside the generated README assets."""
    target = Path(__file__).with_name("architecture.svg")
    tree = ElementTree(build_svg())
    indent(tree)
    tree.write(target, encoding="utf-8", xml_declaration=True)
    print(target)


if __name__ == "__main__":
    main()

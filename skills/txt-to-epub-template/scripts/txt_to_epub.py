from __future__ import annotations

import argparse
import html
import mimetypes
import re
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
HEADING = re.compile(
    r"^(?:第[0-9〇零一二三四五六七八九十百千两]+卷(?:\s|$)|"
    r"第[0-9〇零一二三四五六七八九十百千两]+[章节回](?:\s|$)|"
    r"(?:尾声|终章|后日谈|附录|完本感言)(?:\s|：|:|$)|"
    r"番外(?:[0-9〇零一二三四五六七八九十百千两]+)?(?:\s|：|:|$))"
)
VOLUME = re.compile(r"^第[0-9〇零一二三四五六七八九十百千两]+卷(?:\s|$)")


@dataclass
class Section:
    title: str
    lines: list[str]
    kind: str
    filename: str


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise SystemExit("无法识别 TXT 编码；请先转换为 UTF-8 或 GB18030。")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def split_sections(text: str) -> tuple[list[str], list[Section]]:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    found = [(i, line.strip().lstrip("\ufeff")) for i, line in enumerate(lines) if HEADING.match(line.strip().lstrip("\ufeff"))]
    if not found:
        body = [line for line in lines if line.strip()]
        return [], [Section("正文", body, "chapter", "chapter-0001.xhtml")]
    intro = lines[: found[0][0]]
    sections: list[Section] = []
    chapter_number = 0
    volume_number = 0
    for pos, (start, title) in enumerate(found):
        end = found[pos + 1][0] if pos + 1 < len(found) else len(lines)
        body = lines[start + 1 : end]
        if VOLUME.match(title):
            volume_number += 1
            kind = "volume"
            filename = f"volume-{volume_number:03d}.xhtml"
        else:
            chapter_number += 1
            kind = "chapter"
            filename = f"chapter-{chapter_number:04d}.xhtml"
        sections.append(Section(title, body, kind, filename))
    return intro, sections


def paragraph_html(lines: list[str]) -> str:
    parts: list[str] = []
    for line in lines:
        value = line.strip().lstrip("\ufeff")
        if not value:
            continue
        if re.fullmatch(r"[*＊·•—\-_=]{1,12}", value):
            parts.append("<hr/>")
        else:
            parts.append(f"<p>{esc(value)}</p>")
    return "\n".join(parts)


def xhtml(title: str, stylesheet: str, body: str) -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
<head><meta charset="utf-8"/><title>{esc(title)}</title><link rel="stylesheet" type="text/css" href="../Styles/{stylesheet}"/></head>
<body>{body}</body></html>'''


def nav_html(title: str, sections: list[Section], include_production_note: bool) -> str:
    items: list[str] = ['<li><a href="intro.xhtml">简介</a></li>']
    if include_production_note:
        items.append('<li><a href="production.xhtml">制作说明</a></li>')
    current_volume_open = False
    for section in sections:
        link = f'<a href="{section.filename}">{esc(section.title)}</a>'
        if section.kind == "volume":
            if current_volume_open:
                items.append("</ol></li>")
            items.append(f"<li>{link}<ol>")
            current_volume_open = True
        elif current_volume_open:
            items.append(f"<li>{link}</li>")
        else:
            items.append(f"<li>{link}</li>")
    if current_volume_open:
        items.append("</ol></li>")
    body = f'<nav epub:type="toc" id="toc" xmlns:epub="http://www.idpf.org/2007/ops"><h1>{esc(title)}·目录</h1><ol>{"".join(items)}</ol></nav>'
    return xhtml(f"{title}·目录", "Navigation.css", body)


def svg_cover(title: str, author: str) -> bytes:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#17131d"/><stop offset="1" stop-color="#4d2e20"/></linearGradient></defs>
<rect width="1200" height="1600" fill="url(#g)"/><rect x="90" y="90" width="1020" height="1420" fill="none" stroke="#b89a6a" stroke-width="4"/>
<text x="600" y="680" fill="#f0e6d5" font-size="92" text-anchor="middle" font-family="serif">{esc(title)}</text>
<text x="600" y="850" fill="#c9bda9" font-size="44" text-anchor="middle" font-family="serif">{esc(author)}</text></svg>'''
    return svg.encode("utf-8")


def cover_html(title: str, cover_name: str) -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink" xml:lang="zh-CN" lang="zh-CN">
<head><meta charset="utf-8"/><title>{esc(title)}</title><link rel="stylesheet" type="text/css" href="../Styles/Cover.css"/></head>
<body><div class="cover-page"><svg xmlns="http://www.w3.org/2000/svg" height="100%" width="100%" viewBox="0 0 1200 1600" preserveAspectRatio="xMidYMid meet"><image width="1200" height="1600" preserveAspectRatio="xMidYMid meet" xlink:href="../Images/{esc(cover_name)}"/></svg></div></body>
</html>'''


def production_html(
    title: str, author: str, team: str, provider: str, edition: str,
    production_date: str, layout_reference: str,
) -> str:
    body = f'''<div class="zhizuodB1">
<h2 class="zhizuohB1"><b>•制作•说明•</b></h2>
<hr class="line"/>
<p class="zhizuopB1"><b>•{esc(title)}•</b><br/><span class="zhizuosB1">{esc(author)}◎著</span></p>
<p class="zhizuopB2"><b>•制作团队：{esc(team)}•</b><br/><span class="zhizuosB2"><b>版本{esc(edition)}<br/><span class="zhizuosB3">（{esc(production_date)}）</span></b></span></p>
<hr class="line"/>
<p class="zhizuopB3"><b>制作说明：</b>本书来自<span class="zhizuosB4">{esc(provider)}</span>提供的校对版。</p>
<p class="zhizuopB4">排版参考：{esc(layout_reference)}的优秀排版。</p>
</div>'''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
<head><meta charset="utf-8"/><title>制作说明</title><link rel="stylesheet" type="text/css" href="../Styles/Production.css"/></head>
<body class="zhizuobB1">{body}</body></html>'''


def introduction_html(description: str) -> str:
    paragraphs = [line.strip() for line in description.splitlines() if line.strip()]
    if not paragraphs:
        paragraphs = ["暂无简介"]
    content = "\n".join(f'<p class="shuangkuang">{esc(line)}</p>' for line in paragraphs)
    body = f'''<div class="shuang1"><div class="shuang2">
<h1 class="shkuang">简介</h1>
{content}
</div></div>'''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
<head><meta charset="utf-8"/><title>简介</title><link rel="stylesheet" type="text/css" href="../Styles/Introduction.css"/></head>
<body class="zhizuobB1">{body}</body></html>'''


def build(args: argparse.Namespace) -> None:
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f"拒绝覆盖已有文件：{output}")
    text = read_text(source)
    intro_lines, sections = split_sections(text)
    description = args.description or "\n".join(line.strip() for line in intro_lines if line.strip())
    book_id = f"urn:uuid:{uuid.uuid4()}"
    modified = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if args.cover:
        cover_path = Path(args.cover).resolve()
        cover_data = cover_path.read_bytes()
        suffix = cover_path.suffix.lower() or ".jpg"
        cover_name = f"cover{suffix}"
        cover_type = mimetypes.guess_type(cover_name)[0] or "image/jpeg"
    else:
        cover_data = svg_cover(args.title, args.author)
        cover_name = "cover.svg"
        cover_type = "image/svg+xml"

    include_production_note = not args.no_production_note
    production_date = args.production_date or datetime.now().strftime("%Y.%m.%d")
    manifest = [
        '<item id="nav" href="Text/nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="coverpage" href="Text/cover.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="intro" href="Text/intro.xhtml" media-type="application/xhtml+xml"/>',
        f'<item id="cover-image" href="Images/{cover_name}" media-type="{cover_type}" properties="cover-image"/>',
        '<item id="chapter-css" href="Styles/Chapter.css" media-type="text/css"/>',
        '<item id="cover-css" href="Styles/Cover.css" media-type="text/css"/>',
        '<item id="intro-css" href="Styles/Introduction.css" media-type="text/css"/>',
        '<item id="nav-css" href="Styles/Navigation.css" media-type="text/css"/>',
        '<item id="volume-css" href="Styles/Volume.css" media-type="text/css"/>',
        '<item id="production-css" href="Styles/Production.css" media-type="text/css"/>',
    ]
    spine = ['<itemref idref="coverpage" linear="no"/>', '<itemref idref="intro"/>']
    if include_production_note:
        manifest.append('<item id="production" href="Text/production.xhtml" media-type="application/xhtml+xml"/>')
        spine.append('<itemref idref="production"/>')
    for i, section in enumerate(sections, 1):
        item_id = f"sec{i:04d}"
        manifest.append(f'<item id="{item_id}" href="Text/{section.filename}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{item_id}"/>')

    opf = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="BookId">{book_id}</dc:identifier><dc:title>{esc(args.title)}</dc:title><dc:creator>{esc(args.author)}</dc:creator><dc:language>{esc(args.language)}</dc:language><dc:description>{esc(description)}</dc:description><meta property="dcterms:modified">{modified}</meta></metadata>
<manifest>{''.join(manifest)}</manifest><spine>{''.join(spine)}</spine></package>'''
    container = '''<?xml version="1.0" encoding="utf-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''
    cover_page = cover_html(args.title, cover_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/Text/nav.xhtml", nav_html(args.title, sections, include_production_note))
        zf.writestr("OEBPS/Text/cover.xhtml", cover_page)
        zf.writestr("OEBPS/Text/intro.xhtml", introduction_html(description))
        if include_production_note:
            zf.writestr(
                "OEBPS/Text/production.xhtml",
                production_html(
                    args.title, args.author, args.production_team, args.source_provider,
                    args.edition, production_date, args.layout_reference,
                ),
            )
        for section in sections:
            if section.kind == "volume":
                body = f'<main class="volume-page"><h1 class="volume-title">{esc(section.title)}</h1><hr class="volume-divider"/></main>'
                page = xhtml(section.title, "Volume.css", body)
            else:
                page = xhtml(section.title, "Chapter.css", f'<h1>{esc(section.title)}</h1>{paragraph_html(section.lines)}')
            zf.writestr(f"OEBPS/Text/{section.filename}", page)
        zf.writestr(f"OEBPS/Images/{cover_name}", cover_data)
        for css in ("Chapter.css", "Cover.css", "Introduction.css", "Navigation.css", "Volume.css", "Production.css"):
            zf.writestr(f"OEBPS/Styles/{css}", (ASSETS / css).read_bytes())
    volumes = sum(section.kind == "volume" for section in sections)
    chapters = sum(section.kind == "chapter" for section in sections)
    print(f"输出：{output}")
    print(f"识别：{volumes} 卷，{chapters} 个正文段落")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将中文小说 TXT 转换为 EPUB 3")
    parser.add_argument("input", help="TXT 原稿")
    parser.add_argument("--title", required=True, help="书名")
    parser.add_argument("--author", required=True, help="作者")
    parser.add_argument("--output", required=True, help="输出 EPUB；不得已存在")
    parser.add_argument("--cover", help="可选封面图片")
    parser.add_argument("--description", help="可选简介；默认使用首章前文字")
    parser.add_argument("--language", default="zh-CN", help="语言，默认 zh-CN")
    parser.add_argument("--production-team", default="黑背雪", help="制作团队，默认黑背雪")
    parser.add_argument("--source-provider", default="网友", help="校对版提供者，默认网友")
    parser.add_argument("--edition", default="1.0", help="制作版本，默认 1.0")
    parser.add_argument("--production-date", help="制作日期，默认当天，格式建议 YYYY.MM.DD")
    parser.add_argument("--layout-reference", default="鬼鬼、湖心溪露等大佬", help="排版参考致谢")
    parser.add_argument("--no-production-note", action="store_true", help="不生成制作说明页")
    return parser.parse_args()


if __name__ == "__main__":
    build(parse_args())

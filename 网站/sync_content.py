#!/usr/bin/env python3
"""Build MkDocs pages from the canonical manuscripts.

The manuscripts in ../书稿 are the only editable source. This script splits
multi-chapter Markdown files at level-one headings and writes generated pages
to ./docs in a stable reading order.
"""

from pathlib import Path
from typing import List, Optional
import re
import shutil


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "书稿"
DOCS = HERE / "docs"


BOOKS = [
    {
        "directory": "01-perception",
        "title": "第一册 · 现代视觉算法",
        "description": "卷积，检测分割与视觉骨干。",
        "source": "第一册 现代视觉算法",
        "files": [
            "00 目录总览.md",
        ],
    },
    {
        "directory": "02-vlm",
        "title": "第二册 · 视觉语言建模",
        "description": "CLIP，连接器与视觉语言模型。",
        "source": "第二册 视觉语言建模",
        "files": [
            "00 目录总览.md",
        ],
    },
    {
        "directory": "03-generation",
        "title": "第三册 · 视觉生成",
        "description": "生成基础，图像与视频生成，空间生成与训练推理。",
        "source": "第三册 视觉生成",
        "files": [
            "00 目录总览.md",
            "序章 案例：视觉生成.md",
            "第一部分 生成基础/导读.md",
            "第一部分 生成基础/第1章 基础数学.md",
            "第一部分 生成基础/第2章 对抗生成.md",
            "第一部分 生成基础/第3章 视觉表示.md",
            "第一部分 生成基础/第4章 扩散模型.md",
            "第一部分 生成基础/第5章 分数匹配与流生成.md",
            "第二部分 生成方法/导读.md",
            "第二部分 生成方法/第6章 采样方法.md",
            "第二部分 生成方法/第7章 少步生成与蒸馏.md",
            "第二部分 生成方法/第8章 视觉自回归.md",
            "第二部分 生成方法/第9章 掩码生成.md",
            "第三部分 图像生成/导读.md",
            "第三部分 图像生成/第10章 条件生成.md",
            "第三部分 图像生成/第11章 Transformer生成架构.md",
            "第三部分 图像生成/第12章 像素生成.md",
            "第三部分 图像生成/第13章 图像编辑.md",
            "第三部分 图像生成/第14章 主体适配.md",
            "第三部分 图像生成/第15章 统一模型.md",
            "第四部分 视频生成/导读.md",
            "第四部分 视频生成/第16章 视频表示.md",
            "第四部分 视频生成/第17章 视频模型.md",
            "第四部分 视频生成/第18章 运动控制.md",
            "第四部分 视频生成/第19章 长视频.md",
            "第四部分 视频生成/第20章 多镜头.md",
            "第四部分 视频生成/第21章 音视频.md",
            "第四部分 视频生成/第22章 视频编辑.md",
            "第五部分 空间生成/导读.md",
            "第五部分 空间生成/第23章 三维生成.md",
            "第五部分 空间生成/第24章 交互生成.md",
            "第六部分 训练与推理/导读.md",
            "第六部分 训练与推理/第25章 训练方法.md",
            "第六部分 训练与推理/第26章 生成评测.md",
            "第六部分 训练与推理/第27章 推理优化.md",
            "附录/附录A 概率与变分.md",
            "附录/附录B 连续生成.md",
            "附录/附录C 公式与记号.md",
            "附录/附录D 最小实现.md",
        ],
    },
]


# 第三册全文同步；第一、二册尚在编纂
ACTIVE_BOOK_DIRS = {"03-generation"}
COMING_SOON_DIRS = ("01-perception", "02-vlm")
HOME = """\
---
hide:
  - navigation
  - toc
---

# 现代视觉模型

<div class="book-list">
  <a href="01-perception/">第一册 · 现代视觉算法</a>
  <a href="02-vlm/">第二册 · 视觉语言建模</a>
  <a href="03-generation/">第三册 · 视觉生成</a>
</div>
"""

COMING_SOON = """\
---
hide:
  - navigation
  - toc
---

<div class="coming-soon-page" markdown="0">
  <p class="coming-soon-label">尚在编纂</p>
</div>
"""


def split_h1(markdown):
    """Split Markdown into complete sections starting with a level-one heading.

    Headings inside fenced code blocks (``` ... ```) are ignored, so Python
    comments like ``# continue training`` do not become separate pages.
    """
    matches = []
    in_fence = False
    for match in re.finditer(r"(?m)^(```.*|# (?!#)(.+?))\s*$", markdown):
        line = match.group(0)
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        title = match.group(2)
        if title is None:
            continue
        matches.append((match.start(), title.strip()))
    if not matches:
        return []
    sections = []
    for index, (start, title) in enumerate(matches):
        end = matches[index + 1][0] if index + 1 < len(matches) else len(markdown)
        sections.append((title, markdown[start:end].strip() + "\n"))
    return sections


def front_matter(title):
    safe = title.replace('"', '\\"')
    return f'---\ntitle: "{safe}"\n---\n\n'


def write_text(path, text, written, changed):
    """Update a generated page only when content changes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written.add(path.resolve())
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    path.write_text(text, encoding="utf-8")
    changed.add(path)


def copy_asset(src, dst, written, changed):
    dst.parent.mkdir(parents=True, exist_ok=True)
    written.add(dst.resolve())
    if dst.exists() and dst.read_bytes() == src.read_bytes():
        return
    shutil.copy2(src, dst)
    changed.add(dst)


def _manuscript_stem_key(filename: str) -> Optional[str]:
    """Stable id for a chapter file when only the title after the stem changes.

    ``序章 一个行程助手在算什么.md`` and ``序章 案例：行程助手.md`` share key
    ``序章``; ``第6章 rope.md`` / ``第6章 位置表示.md`` share ``第6章``.
    """
    if filename.startswith("序章"):
        return "序章"
    if filename.startswith("尾声") or filename.startswith("结语"):
        return "尾声"
    if filename == "导读.md" or filename.startswith("导读"):
        return "导读"
    m = re.match(r"(附录[A-Za-z])", filename)
    if m:
        return m.group(1)
    m = re.match(r"(第\d+章)", filename)
    if m:
        return m.group(1)
    if "目录总览" in filename:
        return "目录总览"
    return None


def resolve_manuscript(source_dir: Path, relative_path: str) -> Path:
    """Resolve a listed manuscript path; tolerate folder and title renames.

    Order: exact path → same filename under 第N部分* → same stem key
    (序章 / 第N章 / 附录X / 导读 / 尾声) in the listed directory, then anywhere
    under the book root.
    """
    direct = source_dir / relative_path
    if direct.is_file():
        return direct

    rel = Path(relative_path)
    name = rel.name
    part_key = None
    if rel.parts:
        m = re.match(r"(第.+?部分)", rel.parts[0])
        if m:
            part_key = m.group(1)

    def _prefer_part(paths: List[Path]) -> List[Path]:
        if not part_key or not paths:
            return paths
        prefer = [
            p
            for p in paths
            if any(
                part.startswith(part_key)
                for part in p.relative_to(source_dir).parts
            )
        ]
        return prefer or paths

    def _finish(candidates: List[Path]) -> Optional[Path]:
        candidates = _prefer_part(candidates)
        if len(candidates) == 1:
            found = candidates[0].relative_to(source_dir).as_posix()
            print(f"[sync] path moved: {relative_path} -> {found}")
            return candidates[0]
        if len(candidates) > 1:
            opts = ", ".join(
                p.relative_to(source_dir).as_posix() for p in candidates
            )
            raise FileNotFoundError(
                f"Ambiguous manuscript for {relative_path!r}; candidates: {opts}"
            )
        return None

    by_name = [p for p in source_dir.rglob(name) if p.is_file()]
    hit = _finish(by_name)
    if hit is not None:
        return hit

    stem_key = _manuscript_stem_key(name)
    if stem_key:
        parent_listed = (source_dir / rel).parent
        same_dir = []
        if parent_listed.is_dir():
            same_dir = [
                p
                for p in parent_listed.iterdir()
                if p.is_file()
                and p.suffix == ".md"
                and _manuscript_stem_key(p.name) == stem_key
            ]
        hit = _finish(same_dir)
        if hit is not None:
            return hit

        by_stem = [
            p
            for p in source_dir.rglob("*.md")
            if p.is_file() and _manuscript_stem_key(p.name) == stem_key
        ]
        # 导读/尾声在多个部分下会撞名：已用 part_key 收窄
        hit = _finish(by_stem)
        if hit is not None:
            return hit

    raise FileNotFoundError(f"Missing manuscript: {direct}")


def materialize_local_images(text, source_path, output_dir, written, changed):
    """Copy relative figure files next to the chapter into docs/<book>/figures/.

    Manuscript may use ``figures/foo.jpg`` (relative to the .md file). Generated
    pages live flat under the book docs dir, so links are rewritten to
    ``figures/<basename>``. Alt text may contain ``]`` (e.g. ``[]``), so parse
    with ``![`` … ``](`` … ``)`` rather than a naive character class.
    """
    parts = []
    i = 0
    while True:
        start = text.find("![", i)
        if start < 0:
            parts.append(text[i:])
            break
        mid = text.find("](", start + 2)
        if mid < 0:
            parts.append(text[i:])
            break
        end = text.find(")", mid + 2)
        if end < 0:
            parts.append(text[i:])
            break
        parts.append(text[i:start])
        alt = text[start + 2 : mid]
        raw = text[mid + 2 : end].strip()
        if raw.startswith(("http://", "https://", "/", "data:")):
            parts.append(text[start : end + 1])
        else:
            path_part = raw.split()[0].strip("\"'")
            src = (source_path.parent / path_part).resolve()
            if not src.is_file():
                raise FileNotFoundError(
                    f"Missing figure for {source_path.name}: {path_part}"
                )
            dst = output_dir / "figures" / src.name
            copy_asset(src, dst, written, changed)
            parts.append(f"![{alt}](figures/{src.name})")
        i = end + 1
    return "".join(parts)


def write_book(book, written, changed):
    source_dir = SOURCE / book["source"]
    output_dir = DOCS / book["directory"]
    page_number = 0
    kept_names = {"index.md"}

    for file_index, relative_path in enumerate(book["files"]):
        source_path = resolve_manuscript(source_dir, relative_path)
        text = materialize_local_images(
            source_path.read_text(encoding="utf-8"),
            source_path,
            output_dir,
            written,
            changed,
        )

        if file_index == 0:
            title = split_h1(text)[0][0]
            # 目录总览：隐藏右侧页内 TOC，避免整册大纲全展开
            index_fm = (
                "---\n"
                f'title: "{title}"\n'
                "hide:\n"
                "  - toc\n"
                "---\n\n"
            )
            write_text(
                output_dir / "index.md",
                index_fm + text,
                written,
                changed,
            )
            continue

        for title, section in split_h1(text):
            page_number += 1
            filename = f"{page_number:02d}.md"
            kept_names.add(filename)
            write_text(
                output_dir / filename,
                front_matter(title) + section,
                written,
                changed,
            )

    if output_dir.exists():
        for path in output_dir.glob("*.md"):
            if path.name not in kept_names:
                path.unlink()
                changed.add(path)


def prune_orphans(written, changed):
    if not DOCS.exists():
        return
    for path in DOCS.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".tmp" or path.name.endswith(".tmp"):
            path.unlink()
            changed.add(path)
            continue
        if path.resolve() not in written:
            path.unlink()
            changed.add(path)
    for path in sorted(DOCS.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def _page_nav_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'(?m)^title:\s*"(.*)"\s*$', text)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    if m:
        return m.group(1).strip()
    return path.stem


def build_nav_yaml() -> str:
    """显式 nav：中文册名，避免侧栏出现 01 architecture。"""
    lines = ["nav:", '  - "现代视觉模型": index.md']
    for book in BOOKS:
        directory = book["directory"]
        if directory not in ACTIVE_BOOK_DIRS:
            continue
        title = book["title"].replace('"', '\\"')
        lines.append(f'  - "{title}":')
        lines.append(f"    - {directory}/index.md")
        pages = sorted((DOCS / directory).glob("[0-9][0-9].md"))
        appendix_open = False
        for page in pages:
            page_title = _page_nav_title(page).replace('"', '\\"')
            is_appendix = page_title.startswith("附录")
            if is_appendix and not appendix_open:
                lines.append('    - "附录":')
                appendix_open = True
            if appendix_open and is_appendix:
                lines.append(
                    f'      - "{page_title}": {directory}/{page.name}'
                )
            else:
                if appendix_open and not is_appendix:
                    appendix_open = False
                lines.append(f'    - "{page_title}": {directory}/{page.name}')
    return "\n".join(lines) + "\n"


def write_mkdocs_nav() -> None:
    mkdocs = HERE / "mkdocs.yml"
    text = mkdocs.read_text(encoding="utf-8")
    begin, end = "# BEGIN_NAV", "# END_NAV"
    block = f"{begin}\n{build_nav_yaml()}{end}"
    if begin in text and end in text:
        text = re.sub(
            re.escape(begin) + r".*?" + re.escape(end),
            block,
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    mkdocs.write_text(text, encoding="utf-8")


def main():
    written = set()
    changed = set()
    (DOCS / "stylesheets").mkdir(parents=True, exist_ok=True)
    (DOCS / "javascripts").mkdir(parents=True, exist_ok=True)
    (DOCS / "assets").mkdir(parents=True, exist_ok=True)

    write_text(DOCS / "index.md", HOME, written, changed)
    copy_asset(
        HERE / "assets" / "favicon.png",
        DOCS / "assets" / "favicon.png",
        written,
        changed,
    )
    copy_asset(
        HERE / "stylesheets" / "extra.css",
        DOCS / "stylesheets" / "extra.css",
        written,
        changed,
    )
    copy_asset(
        HERE / "javascripts" / "mathjax-config.js",
        DOCS / "javascripts" / "mathjax-config.js",
        written,
        changed,
    )
    copy_asset(
        HERE / "javascripts" / "formula-flow.js",
        DOCS / "javascripts" / "formula-flow.js",
        written,
        changed,
    )
    copy_asset(
        HERE / "javascripts" / "vendor" / "tex-mml-chtml.js",
        DOCS / "javascripts" / "vendor" / "tex-mml-chtml.js",
        written,
        changed,
    )

    for book in BOOKS:
        if book["directory"] not in ACTIVE_BOOK_DIRS:
            continue
        write_book(book, written, changed)

    for directory in COMING_SOON_DIRS:
        out = DOCS / directory
        out.mkdir(parents=True, exist_ok=True)
        write_text(out / "index.md", COMING_SOON, written, changed)

    prune_orphans(written, changed)
    write_mkdocs_nav()
    page_count = len(list(DOCS.rglob("*.md")))
    print(
        f"Generated {page_count} Markdown pages in {DOCS}"
        + (f" ({len(changed)} changed)" if changed else " (unchanged)")
    )
    return bool(changed)


if __name__ == "__main__":
    main()

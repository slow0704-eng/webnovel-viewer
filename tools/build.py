"""projects/*/chapters/*.md → web/index.html (단일 파일, 의존성 없음)

    cd web/tools && python build.py
"""
import html, json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "projects"
WEB = ROOT / "web"

# 폴더명 → URL 슬러그 · 표지 색 (진열 순서)
BOOKS = [
    ("제0법정", "courtroom-zero", "#5B1F1F"),
    ("카데바는-학생이었다", "cadaver", "#1F3A3D"),
    ("이름없는-신입생", "nameless", "#2B2547"),
    ("청월학원-결석계", "cheongwol", "#1E3350"),
    ("백운관-304호", "baegun-304", "#2F3B2A"),
    ("서한고-9층", "seohan-9", "#3A2E22"),
]

TIMER = re.compile(r"^\[D-?\d+.*\]$|^\[D-DAY.*\]$")


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r'<span class="sys">\1</span>', s)
    return s


def block(lines):
    # 한 줄 전체가 `...` → 화면/문서 속 텍스트. 타이머는 따로 표시
    if all(l.startswith("`") and l.endswith("`") and l.count("`") == 2 for l in lines):
        inner = [l[1:-1] for l in lines]
        if len(inner) == 1 and TIMER.match(inner[0]):
            return f'<div class="timer">{html.escape(inner[0])}</div>'
        return '<div class="doc">' + "<br>".join(html.escape(x) for x in inner) + "</div>"
    if all(l.startswith("**") and l.endswith("**") for l in lines):
        return '<p class="em-line">' + "<br>".join(inline(l) for l in lines) + "</p>"
    return "<p>" + "<br>".join(inline(l) for l in lines) + "</p>"


def chapter(md):
    title, out, buf = "", [], []

    def flush():
        if buf:
            out.append(block(buf))
            buf.clear()

    for raw in md.splitlines():
        line = raw.strip()
        if line.startswith("<!--"):
            continue
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        if not line:
            flush()
        elif re.fullmatch(r"-{3,}|\*{3,}", line):
            flush()
            out.append('<hr class="scene">')
        else:
            buf.append(line)
    flush()
    m = re.match(r"제\s*(\d+)\s*화\.?\s*(.*)", title)
    sub = m.group(2) if m else title
    text = re.sub(r"<[^>]+>", "", "".join(out))
    return {"title": sub, "html": "\n".join(out), "chars": len(text)}


def field(concept, name):
    m = re.search(rf"\*\*{name}:\*\*\s*(.+)", concept)
    return m.group(1).strip() if m else ""


def main():
    books = []
    for folder, slug, color in BOOKS:
        d = PROJECTS / folder
        concept = (d / "01_concept.md").read_text(encoding="utf-8")
        full = field(concept, "가제").strip("『』")
        main_t, _, sub_t = full.partition(" — ")
        chs = [chapter(p.read_text(encoding="utf-8"))
               for p in sorted((d / "chapters").glob("ch*.md"))]
        notice = re.search(r"^> \*\*고지:\*\*(.+?)(?=\n[^>])", concept, re.S | re.M)
        notice = re.sub(r"\s*\n>\s*", " ", notice.group(1)).replace("**", "").replace("*", "").strip() if notice else ""
        books.append({
            "slug": slug, "color": color,
            "title": main_t, "subtitle": sub_t,
            "genre": field(concept, "장르"),
            "logline": field(concept, "로그라인").replace("**", ""),
            "notice": notice,
            "chapters": chs,
        })
        print(f"{slug}: {len(chs)}화 · {sum(c['chars'] for c in chs):,}자")

    data = json.dumps(books, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")
    tpl = (WEB / "tools" / "template.html").read_text(encoding="utf-8")
    (WEB / "index.html").write_text(tpl.replace("/*__DATA__*/null", data), encoding="utf-8")
    print("→ web/index.html", (WEB / "index.html").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()

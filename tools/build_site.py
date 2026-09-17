"""
Ornithopter — gerador do site estático (GitHub Pages).

Transforma:
  presentation/ornithopter.html  →  site/index.html (capa)
  docs/*.md                      →  site/docs/*.html (renderizados)
  docs/bom.csv                   →  site/bom.html (tabela Excel-like com links)
  assets/*                       →  site/assets/*

Uso:  python tools/build_site.py   (requer: pip install markdown)
"""
from __future__ import annotations

import csv
import html
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

NAV = """
<div class="nav">
  <a href="{root}index.html">✈ Ornithopter</a>
  <a href="{root}bom.html">💰 BOM</a>
  <a href="{root}docs/viability.html">📐 Viabilidade</a>
  <a href="{root}docs/wiring.html">🔌 Ligações</a>
  <a href="{root}docs/ground-station.html">🖥 Estação de solo</a>
  <a href="{root}docs/algorithms.html">🧠 Algoritmos</a>
  <a href="{root}app/README.html">📱 App Expo</a>
  <a href="{root}docs/build-plan.html">🛠 Construção</a>
  <a href="https://github.com/RicardoAEGN1/Ornithopter">GitHub ↗</a>
</div>
"""

STYLE = """
<style>
  :root { --ink:#1e1e1e; --red:#e03131; --blue:#1c7ed6; --paper:#fdfcf8; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--paper); color:var(--ink);
    font-family:'Patrick Hand','Comic Sans MS',cursive; font-size:1.15rem; line-height:1.55;
    background-image:linear-gradient(#e6e2d8 1px,transparent 1px),linear-gradient(90deg,#e6e2d8 1px,transparent 1px);
    background-size:28px 28px; }
  .nav { background:#1e1810; padding:10px 18px; display:flex; gap:18px; flex-wrap:wrap;
    position:sticky; top:0; z-index:9; }
  .nav a { color:#e8a765; text-decoration:none; font-size:1rem; }
  .nav a:hover { color:#ff7b24; }
  main { max-width:900px; margin:0 auto; padding:34px 22px 80px; }
  h1,h2,h3 { font-family:'Gloria Hallelujah','Comic Sans MS',cursive; font-weight:normal; }
  h1 { font-size:2.4rem; } h2 { border-bottom:3px solid var(--ink); display:inline-block; margin-top:40px; }
  table { border-collapse:collapse; width:100%; margin:14px 0; }
  th,td { border:2px solid var(--ink); padding:5px 11px; font-size:1rem; }
  th { background:rgba(28,126,214,.08); }
  code,pre { background:#1e1810; color:#e8dcc8; border-radius:8px; }
  code { padding:2px 6px; } pre { padding:14px; overflow-x:auto; }
  pre code { padding:0; }
  a { color:var(--blue); }
  tr.total td { border-top:3px double var(--ink); font-weight:bold; color:var(--red); }
  blockquote { border-left:4px solid var(--red); margin:14px 0; padding:4px 16px; background:rgba(255,255,255,.6); }
  .foot { text-align:center; color:#888; margin-top:60px; font-size:.95rem; }
</style>
"""

FOOT = '<div class="foot">Ornithopter · Ricardo Alexander, n13 · 11G · <a href="https://github.com/RicardoAEGN1/Ornithopter">github.com/RicardoAEGN1/Ornithopter</a></div>'


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def page(title: str, body: str, root: str = "") -> str:
    nav = NAV.replace("{root}", root)
    return f"""<!DOCTYPE html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Ornithopter</title>{STYLE}</head>
<body>{nav}<main>{body}{FOOT}</main></body></html>"""


def build_docs() -> None:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
    for src in sorted((ROOT / "docs").glob("*.md")):
        md.reset()
        body = md.convert(src.read_text(encoding="utf-8"))
        write(SITE / "docs" / f"{src.stem}.html", page(src.stem.replace("-", " ").title(), body, root="../"))
    # app README também no site
    md.reset()
    body = md.convert((ROOT / "app" / "README.md").read_text(encoding="utf-8"))
    write(SITE / "app" / "README.html", page("App Expo — controlo", body, root="../"))


def build_bom() -> None:
    rows = []
    with (ROOT / "docs" / "bom.csv").open(encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
        for r in reader:
            if not r or r[0].startswith(("TOTAL", "ORCAMENTO", "FOLGA")):
                label = r[0] if r else ""
                value = r[5] if len(r) > 5 else ""
                cls = " class='total'" if label else ""
                rows.append(f"<tr{cls}><td colspan='5'>{label}</td><td>{value}</td></tr>")
                continue
            r = (r + [""] * 7)[:7]
            comp, spec, forn, qtd, unit, sub, link = r
            comp_cell = f"<a href='{html.escape(link)}' target='_blank'>{html.escape(comp)}</a>" if link.startswith("http") else html.escape(comp)
            rows.append(
                f"<tr><td>{comp_cell}</td><td>{html.escape(spec)}</td><td>{html.escape(forn)}</td>"
                f"<td>{html.escape(qtd)}</td><td>{html.escape(unit)}</td><td><b>{html.escape(sub)}</b></td></tr>")
    table = ("<table><tr>" + "".join(
        f"<th>{h}</th>" for h in ["Componente", "Especificação", "Fornecedor", "Qtd", "Preço un.", "Subtotal"]) +
        "</tr>" + "".join(rows) + "</table>")
    intro = ("<h1>💰 Lista de material (BOM)</h1>"
             "<p>Tabela gerada de <code>docs/bom.csv</code> — abre também direto no Excel. "
             "Clica no nome do componente para pesquisar no fornecedor.</p>")
    write(SITE / "bom.html", page("BOM — Lista de material", intro + table))


def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    print("Gerando site…")
    # 1. apresentação como capa
    SITE.mkdir(parents=True)
    shutil.copy(ROOT / "presentation" / "ornithopter.html", SITE / "index.html")
    print("  ✓ site/index.html (apresentação)")
    # 2. docs e bom
    build_docs()
    build_bom()
    # 3. assets
    shutil.copytree(ROOT / "assets", SITE / "assets", dirs_exist_ok=True)
    print("  ✓ site/assets/")
    print(f"Pronto → {SITE}")


if __name__ == "__main__":
    main()

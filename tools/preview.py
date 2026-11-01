#!/usr/bin/env python3
"""Renders README.md with GitHub's markdown API and shows it twice, in GitHub's
light and dark styles, side by side. Writes README.preview.html (gitignored).
"""
import os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDN = "https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/"

body = subprocess.run(["gh", "api", "markdown", "-f", "mode=gfm", "-f", "context=arjanchaudharyy/arjanchaudharyy",
                       "-F", f"text=@{os.path.join(ROOT, 'README.md')}"], capture_output=True, text=True, check=True).stdout


def force(theme):
    # a <picture> follows the page's colour scheme; pin each panel to one theme
    b = re.sub(r'<source[^>]*>', '', body)
    return b.replace("-light.svg", f"-{theme}.svg")


page = f"""<!doctype html><meta charset=utf-8><title>README.md</title>
<link rel=stylesheet href="{CDN}github-markdown-light.min.css">
<style>body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;background:#e9e9e6}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:0;min-height:100vh}}.pane{{padding:40px 32px}}
.pane>h6{{font:500 11px ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;margin:0 auto 14px;max-width:880px;color:#8a8a85}}
.markdown-body{{max-width:880px;margin:0 auto;padding:32px;border:1px solid #d0d7de;border-radius:6px}}
.light{{background:#fff}}.dark{{background:#0d1117}}
.dark .markdown-body{{background:#0d1117;color:#e6edf3;border-color:#30363d}}.dark .markdown-body a{{color:#4493f8}}
.dark details summary{{color:#e6edf3}}
@media (max-width:1100px){{.row{{grid-template-columns:1fr}}}}</style>
<div class=row><div class="pane light"><h6>readme.md / light</h6><article class=markdown-body>{force("light")}</article></div>
<div class="pane dark"><h6>readme.md / dark</h6><article class=markdown-body>{force("dark")}</article></div></div>"""
with open(os.path.join(ROOT, "README.preview.html"), "w") as f:
    f.write(page)
print(os.path.join(ROOT, "README.preview.html"))

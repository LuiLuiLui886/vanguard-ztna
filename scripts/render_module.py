#!/usr/bin/env python3
"""Render the usage module to a standalone, printable HTML document."""

import argparse
import base64
import re
from html import escape
from pathlib import Path

from markdown_it import MarkdownIt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    renderer = MarkdownIt('commonmark', {'html': False}).enable('table')
    source = args.source.read_text(encoding='utf-8')
    tokens = renderer.parse(source)
    contents = []
    chapter = 0
    for index, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag in ('h2', 'h3', 'h4'):
            label = tokens[index + 1].content
            if token.tag == 'h2':
                chapter += 1
                anchor = f'bab-{chapter}'
            else:
                number = re.match(r'\d+(?:\.\d+)+', label)
                suffix = number[0].replace('.', '-') if number else str(len(contents) + 1)
                anchor = f'bagian-{suffix}'
            token.attrSet('id', anchor)
            contents.append((anchor, label, token.tag))
    navigation = '<nav aria-label="Daftar isi"><h2>Daftar isi</h2><ol>' + ''.join(
        f'<li class="toc-{level}"><a href="#{anchor}">{escape(label)}</a></li>'
        for anchor, label, level in contents) + '</ol></nav>'
    # Keep relative documentation links valid when HTML is beside the Markdown.
    body = renderer.renderer.render(tokens, renderer.options, {})
    # Embed the manual's static flowcharts so copied HTML stays fully offline.
    def embed_flow(match):
        data = (args.source.parent / match[1]).read_bytes()
        return 'src="data:image/svg+xml;base64,' + base64.b64encode(data).decode('ascii') + '"'
    body = re.sub(r'src="(assets/flows/[a-z0-9-]+\.svg)"', embed_flow, body)
    body = body.replace('</h1>', '</h1>' + navigation, 1)
    title = escape(source.splitlines()[0].lstrip('# '))
    css = '''
body { font: 16px/1.65 system-ui,sans-serif; color:#172536; background:#eef2f6;
       margin:0; padding:2rem; }
main { max-width:980px; margin:auto; padding:3rem; background:white; }
h1,h2,h3,h4 { line-height:1.25; color:#12465a; }
nav ol { list-style:none; padding-left:0; }
.toc-h2 { margin-top:.5rem; font-weight:600; }
.toc-h3 { margin-left:1rem; } .toc-h4 { margin-left:2rem; }
h1 { font-size:2.2rem; } h2 { margin-top:2.8rem; border-bottom:2px solid #dae5e9;
                            padding-bottom:.5rem; }
a { color:#075b83; } table { width:100%; border-collapse:collapse; margin:1rem 0; }
th,td { border:1px solid #ccd7dd; padding:.5rem; text-align:left; vertical-align:top; }
th { background:#edf5f6; } pre { background:#f1f5f7; padding:1rem;
                             white-space:pre-wrap; overflow-wrap:anywhere; }
img { max-width:100%; height:auto; }
code { font-size:.9em; } blockquote { border-left:4px solid #1c7088; margin-left:0;
                                    padding-left:1rem; }
.print-note { border:1px solid #c7dbe4; padding:1rem; background:#f3f8fa; }
@page { size:A4; margin:18mm; }
@media print {
 body { background:white; padding:0; font-size:10pt; }
 main { padding:0; max-width:none; }
 h2,h3,h4 { break-after:avoid; } h2 { margin-top:1.8rem; }
 pre,tr { break-inside:avoid; } thead { display:table-header-group; }
 a { color:inherit; } .print-note { display:none; }
}
'''
    args.output.write_text(
        '<!doctype html>\n<html lang="id"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{title}</title><style>{css}</style></head><body><main>'
        '<p class="print-note">Modul dapat dibaca tanpa internet. Untuk PDF, '
        'tekan Ctrl+P, pilih Simpan sebagai PDF, ukuran A4. Tautan dokumen '
        'pendukung memerlukan folder docs dari repository yang sama.</p>'
        f'{body}</main></body></html>\n', encoding='utf-8')


if __name__ == '__main__':
    main()

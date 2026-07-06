"""
Google Drive utility — create folders and upload files.

Usage:
  python -B drive.py create-folder "Folder Name"
  python -B drive.py create-folder "Subfolder" --parent FOLDER_ID
  python -B drive.py create-doc "Doc Name"
  python -B drive.py create-doc "Doc Name" --parent FOLDER_ID
  python -B drive.py create-sheet "Sheet Name"
  python -B drive.py create-sheet "Sheet Name" --parent FOLDER_ID
  python -B drive.py upload "C:/path/to/file.pdf"
    python -B drive.py upload "C:/path/to/file.pdf" --parent FOLDER_ID
    python -B drive.py upload "C:/path/to/file.pdf" --parent FOLDER_ID --name "Custom Name.pdf"
  python -B drive.py write-markdown-to-doc DOC_ID --files path1.md [path2.md ...]

Use append_rows() in scripts (not the Sheets API append directly) to add data rows without
inheriting header formatting. See append_rows() docstring for details.

Use draft_rows() in temp scripts to write drafts into specific cells of an existing sheet.
Pass a list of (A1-notation range, value) tuples — e.g. [('Sheet1!D2', 'My text'), ...].

Run setup_auth.py first to authenticate.
The -B flag suppresses __pycache__ creation.
"""

import argparse
import csv
import os
import re
import urllib.parse
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from microcopy_scope import (
    MICROCOPY_HEADERS,
    HEADER_ROW_HEIGHT,
    CELL_TEXT_FORMAT,
    CELL_VERTICAL_ALIGNMENT,
    CELL_HORIZONTAL_ALIGNMENT,
    CELL_WRAP_STRATEGY,
    _GRAY,
    _RED,
)

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'token.json')


def _get_creds():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError("No valid credentials found. Run setup_auth.py first.")
    return creds


def get_service():
    return build('drive', 'v3', credentials=_get_creds())


def get_sheets_service():
    return build('sheets', 'v4', credentials=_get_creds())


def get_docs_service():
    return build('docs', 'v1', credentials=_get_creds())


def read_doc(doc_id):
    """Read a Google Doc and return its plain text content."""
    service = get_docs_service()
    doc = service.documents().get(documentId=doc_id).execute(num_retries=5)
    lines = []
    for block in doc.get('body', {}).get('content', []):
        para = block.get('paragraph')
        if not para:
            continue
        text = ''.join(
            el.get('textRun', {}).get('content', '')
            for el in para.get('elements', [])
        )
        lines.append(text)
    return ''.join(lines)


def create_folder(name, parent_id=None):
    """Create a folder in Drive. Returns the folder ID."""
    service = get_service()
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        metadata['parents'] = [parent_id]
    folder = service.files().create(body=metadata, fields='id, name').execute(num_retries=5)
    url = f"https://drive.google.com/drive/folders/{folder['id']}"
    print(f"Created folder '{folder['name']}' — id: {folder['id']} — url: {url}")
    return folder['id']


def create_doc(name, parent_id=None):
    """Create an empty Google Doc in Drive. Returns (file_id, url)."""
    service = get_service()
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.document',
    }
    if parent_id:
        metadata['parents'] = [parent_id]
    doc = service.files().create(body=metadata, fields='id, name').execute(num_retries=5)
    url = f"https://docs.google.com/document/d/{doc['id']}/edit"
    print(f"Created doc '{doc['name']}' — id: {doc['id']} — url: {url}")
    return doc['id'], url


def create_sheet(name, parent_id=None):
    """Create a Google Sheet in Drive with microcopy headers. Returns (file_id, url)."""
    service = get_service()
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.spreadsheet',
    }
    if parent_id:
        metadata['parents'] = [parent_id]
    sheet = service.files().create(body=metadata, fields='id, name').execute(num_retries=5)
    sheet_id = sheet['id']
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

    base_text_format = {
        **CELL_TEXT_FORMAT,
        'bold': False,
    }
    base_format = {
        'textFormat': base_text_format,
        'verticalAlignment': CELL_VERTICAL_ALIGNMENT,
        'horizontalAlignment': CELL_HORIZONTAL_ALIGNMENT,
        'wrapStrategy': CELL_WRAP_STRATEGY,
    }

    cell_values = [
        {
            'userEnteredValue': {'stringValue': header},
            'userEnteredFormat': {
                **base_format,
                'textFormat': {**base_text_format, 'bold': True},
                'backgroundColor': color,
            },
        }
        for header, color, _ in MICROCOPY_HEADERS
    ]

    requests = [
        # Base formatting for all data rows
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 1,
                    'endRowIndex': 1000,
                    'startColumnIndex': 0,
                    'endColumnIndex': len(MICROCOPY_HEADERS),
                },
                'cell': {'userEnteredFormat': base_format},
                'fields': 'userEnteredFormat.textFormat,userEnteredFormat.verticalAlignment,userEnteredFormat.horizontalAlignment,userEnteredFormat.wrapStrategy',
            }
        },
        # Header row cells
        {
            'updateCells': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': len(MICROCOPY_HEADERS),
                },
                'rows': [{'values': cell_values}],
                'fields': 'userEnteredValue,userEnteredFormat.textFormat,userEnteredFormat.verticalAlignment,userEnteredFormat.horizontalAlignment,userEnteredFormat.wrapStrategy,userEnteredFormat.backgroundColor',
            }
        },
        # Header row height
        {
            'updateDimensionProperties': {
                'range': {'sheetId': 0, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': 1},
                'properties': {'pixelSize': HEADER_ROW_HEIGHT},
                'fields': 'pixelSize',
            }
        },
    ]

    # Column widths
    for col_idx, (_, _, col_width) in enumerate(MICROCOPY_HEADERS):
        requests.append({
            'updateDimensionProperties': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': col_idx,
                    'endIndex': col_idx + 1,
                },
                'properties': {'pixelSize': col_width},
                'fields': 'pixelSize',
            }
        })

    # Conditional formatting for "New" column (index 3), rows 2-1000
    # Rule 1: Light red background if cell is empty
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [
                    {
                        'sheetId': 0,
                        'startColumnIndex': 3,
                        'endColumnIndex': 4,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                    }
                ],
                'booleanRule': {
                    'condition': {'type': 'BLANK'},
                    'format': {'backgroundColor': _RED},
                }
            },
            'index': 0,
        }
    })

    # Rule 2: Italic gray text if cell equals "No change"
    requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [
                    {
                        'sheetId': 0,
                        'startColumnIndex': 3,
                        'endColumnIndex': 4,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                    }
                ],
                'booleanRule': {
                    'condition': {
                        'type': 'CUSTOM_FORMULA',
                        'values': [{'userEnteredValue': '=D2="No change"'}]
                    },
                    'format': {
                        'textFormat': {'italic': True, 'foregroundColor': _GRAY}
                    },
                }
            },
            'index': 1,
        }
    })

    get_sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': requests},
    ).execute(num_retries=5)

    print(f"Created sheet '{sheet['name']}' — id: {sheet_id} — url: {url}")
    return sheet_id, url


def append_rows(sheet_id, rows, sheet_tab_id=0):
    """Append rows to a microcopy sheet and reset formatting to plain.

    Args:
        sheet_id: Google Sheets file ID.
        rows: List of lists of cell values.
        sheet_tab_id: Integer sheet tab ID (default 0 = first tab).
    """
    svc = get_sheets_service()
    num_cols = len(MICROCOPY_HEADERS)

    # Append values
    result = svc.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range='Sheet1!A1',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': rows},
    ).execute(num_retries=5)

    updated = result.get('updates', {})
    print(f"Appended {updated.get('updatedRows', 0)} row(s) to {updated.get('updatedRange', '?')}")

    # Determine which rows were written and clear their formatting
    updated_range = updated.get('updatedRange', '')
    # e.g. "Sheet1!A5:E7" → start row index = 4 (0-based), end = 7
    import re
    m = re.search(r'!A(\d+):', updated_range)
    if m:
        start_row = int(m.group(1)) - 1  # convert to 0-based
        end_row = start_row + len(rows)

        plain_format = {
            'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
            'textFormat': {**CELL_TEXT_FORMAT, 'bold': False},
            'verticalAlignment': CELL_VERTICAL_ALIGNMENT,
            'horizontalAlignment': CELL_HORIZONTAL_ALIGNMENT,
            'wrapStrategy': CELL_WRAP_STRATEGY,
        }
        svc.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': [{
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_tab_id,
                        'startRowIndex': start_row,
                        'endRowIndex': end_row,
                        'startColumnIndex': 0,
                        'endColumnIndex': num_cols,
                    },
                    'cell': {'userEnteredFormat': plain_format},
                    'fields': 'userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.verticalAlignment,userEnteredFormat.horizontalAlignment,userEnteredFormat.wrapStrategy',
                }
            }]},
        ).execute(num_retries=5)
        print("Formatting reset to plain.")


def draft_rows(sheet_id, cell_values):
    """Write draft values into specific cells of an existing sheet.

    Args:
        sheet_id:    Google Sheets file ID.
        cell_values: List of (A1-notation range, value) tuples.
                     e.g. [('Sheet1!D2', 'My text'), ('Sheet1!E2', 'A note')]
    """
    svc = get_sheets_service()
    body = {
        'valueInputOption': 'RAW',
        'data': [{'range': r, 'values': [[v]]} for r, v in cell_values],
    }
    result = svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body=body,
    ).execute(num_retries=5)
    print(f"Updated {result.get('totalUpdatedCells', 0)} cells")



def upload_file(local_path, parent_id=None, name=None):
    """Upload a file to Drive. Returns the file ID."""
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"File not found: {local_path}")
    service = get_service()
    file_name = name or os.path.basename(local_path)
    metadata = {'name': file_name}
    if parent_id:
        metadata['parents'] = [parent_id]
    media = MediaFileUpload(local_path, resumable=True)
    f = service.files().create(body=metadata, media_body=media, fields='id, name').execute(num_retries=5)
    print(f"Uploaded '{f['name']}' — id: {f['id']}")
    return f['id']


# ─────────────────────────────────────────────────────────────────────────────
# Markdown → Google Docs conversion
# ─────────────────────────────────────────────────────────────────────────────

# Colour palette (RGB 0–1) for callout-block backgrounds
_BG_NOTE         = {'red': 1.00, 'green': 0.95, 'blue': 0.80}   # amber
_BG_WARNING      = {'red': 1.00, 'green': 0.80, 'blue': 0.80}   # red
_BG_OVERVIEW     = {'red': 0.85, 'green': 0.92, 'blue': 1.00}   # blue
_BG_SNIPPET      = {'red': 0.91, 'green': 0.96, 'blue': 0.91}   # green
_BG_IMAGE        = {'red': 1.00, 'green': 1.00, 'blue': 0.60}   # yellow
_BG_TABLE_HEADER = {'red': 0.90, 'green': 0.90, 'blue': 0.90}   # light grey

_BLOCK_BG = {
    'note':     _BG_NOTE,
    'warning':  _BG_WARNING,
    'overview': _BG_OVERVIEW,
    'snippet':  _BG_SNIPPET,
}

# Compiled regex for inline markdown elements.
# Groups: bold_italic, bold, italic, img_alt, img_src, link_text, link_url, code
_INLINE_RE = re.compile(
    r'\*\*\*(.+?)\*\*\*'              # 1: bold-italic  ***text***
    r'|\*\*(.+?)\*\*'                  # 2: bold         **text**
    r'|\*([^*\n]+?)\*'                # 3: italic       *text*
    r'|!\[([^\]]*)\]\(([^)]*)\)'      # 4,5: image      ![alt](src)
    r'|\[([^\]]+)\]\(([^)]*)\)'       # 6,7: link       [text](url)
    r'|`([^`\n]+)`'                   # 8: inline code  `code`
)


def _load_kb_url_map(md_path):
    """Load _Metadata/URLs.csv for the product that owns md_path.

    Detects the product (Core or Omni) by finding that directory name in the
    file path.  Returns {lowercase_filename_without_ext: zendesk_url}.
    Returns {} if the CSV cannot be located.
    """
    parts = Path(md_path).resolve().parts
    for i, part in enumerate(parts):
        if part in ('Core', 'Omni'):
            csv_path = Path(*parts[:i + 1]) / '_Metadata' / 'URLs.csv'
            if csv_path.exists():
                url_map = {}
                with open(csv_path, newline='', encoding='utf-8') as f:
                    for row in csv.DictReader(f):
                        fname = (row.get('filename') or '').strip()
                        url   = (row.get('url')      or '').strip()
                        if fname and url:
                            url_map[fname.lower()] = url
                return url_map
            break
    return {}


def _preprocess_markdown_links(content, url_map):
    """Replace intra-KB markdown links [text](Filename.md) with Zendesk URLs.

    Handles URL-encoded filenames (spaces as %20).  Links not found in url_map
    are left unchanged.
    """
    if not url_map:
        return content

    def _replace(m):
        text, href = m.group(1), m.group(2)
        if not href.lower().endswith('.md'):
            return m.group(0)
        stem = urllib.parse.unquote(href)[:-3]   # strip .md
        url = url_map.get(stem.lower())
        return f'[{text}]({url})' if url else m.group(0)

    return re.sub(r'\[([^\]]+)\]\(([^)]*)\)', _replace, content)


def _parse_inline(text, para_bg=None):
    """Parse inline markdown into a list of run dicts.

    Each dict may contain: text (str), bold (bool), italic (bool),
    link (str URL), bg_color (RGB dict), font (str family name).

    Underscore emphasis (_italic_) is intentionally not supported —
    underscores appear in KB filenames and MadCap variable names.
    """
    runs = []
    last = 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > last:
            plain = text[last:m.start()]
            if plain:
                runs.append({'text': plain})
        g = m.groups()
        if g[0]:                     # ***bold-italic***
            runs.append({'text': g[0], 'bold': True, 'italic': True})
        elif g[1]:                   # **bold**
            runs.append({'text': g[1], 'bold': True})
        elif g[2]:                   # *italic*
            runs.append({'text': g[2], 'italic': True})
        elif g[3] is not None:       # ![alt](src)
            src = g[4] or ''
            fname = Path(urllib.parse.unquote(src)).name if src else 'image'
            runs.append({'text': f'[Image: {fname}]', 'bg_color': _BG_IMAGE})
        elif g[5]:                   # [text](url)
            runs.append({'text': g[5], 'link': g[6] or ''})
        elif g[7]:                   # `code`
            runs.append({'text': g[7], 'font': 'Courier New'})
        last = m.end()
    if last < len(text):
        remaining = text[last:]
        if remaining:
            runs.append({'text': remaining})
    if not runs:
        runs = [{'text': text}]
    # Apply paragraph-level background to runs that don't have their own
    if para_bg:
        for r in runs:
            if 'bg_color' not in r and r.get('text', '').strip():
                r['bg_color'] = para_bg
    return runs


def _parse_markdown_to_paras(content):
    """Parse markdown content into a flat list of paragraph dicts.

    Each dict has:
      style   – 'HEADING_1' .. 'HEADING_4' | 'NORMAL_TEXT'
      runs    – list of run dicts from _parse_inline()
      list    – None | 'BULLET' | 'NUMBERED'
      nesting – int, 0-based indent level for list items
      table   – None | list of {'cells': [...], 'is_header': bool}
      para_bg – None | RGB dict for callout-block paragraph shading
    """
    lines = content.splitlines()
    paras = []
    i = 0
    in_block = None
    block_lines = []
    pending = []        # accumulate multi-line paragraph text

    def flush():
        if not pending:
            return
        text = ' '.join(ln.strip() for ln in pending if ln.strip())
        pending.clear()
        if text:
            paras.append({
                'style': 'NORMAL_TEXT',
                'runs': _parse_inline(text),
                'list': None, 'nesting': 0,
                'table': None, 'para_bg': None,
            })

    while i < len(lines):
        line = lines[i]

        # ── ::: block open ────────────────────────────────────────────────────
        m = re.match(r'^:::([\w]+)(?:\s+src="[^"]*")?', line.strip())
        if m and in_block is None:
            flush()
            in_block = m.group(1)
            block_lines = []
            i += 1
            continue

        # ── ::: block close ───────────────────────────────────────────────────
        if line.strip() == ':::' and in_block is not None:
            bg = _BLOCK_BG.get(in_block)
            for bl in block_lines:
                bl = bl.strip()
                if not bl:
                    continue
                hm = re.match(r'^(#{1,4})\s+(.+)', bl)
                if hm:
                    runs = _parse_inline(hm.group(2).strip(), para_bg=bg)
                    runs = [dict(r, bold=True) for r in runs]
                else:
                    runs = _parse_inline(bl, para_bg=bg)
                paras.append({
                    'style': 'NORMAL_TEXT', 'runs': runs,
                    'list': None, 'nesting': 0,
                    'table': None, 'para_bg': bg,
                })
            in_block = None
            block_lines = []
            i += 1
            continue

        if in_block is not None:
            block_lines.append(line)
            i += 1
            continue

        # ── HTML comments ─────────────────────────────────────────────────────
        if line.strip().startswith('<!--'):
            i += 1
            continue

        # ── Blank line ────────────────────────────────────────────────────────
        if not line.strip():
            flush()
            i += 1
            continue

        # ── Headings (H1–H4) ─────────────────────────────────────────────────
        hm = re.match(r'^(#{1,4})\s+(.+)', line)
        if hm:
            flush()
            level = len(hm.group(1))
            paras.append({
                'style': f'HEADING_{level}',
                'runs': _parse_inline(hm.group(2).strip()),
                'list': None, 'nesting': 0,
                'table': None, 'para_bg': None,
            })
            i += 1
            continue

        # ── Tables ────────────────────────────────────────────────────────────
        if re.match(r'^\s*\|', line):
            flush()
            rows = []
            while i < len(lines) and re.match(r'^\s*\|', lines[i]):
                row = lines[i].strip()
                if re.match(r'^\|[\s|:\-]+\|$', row):   # separator row
                    if rows:
                        rows[-1]['is_header'] = True
                    i += 1
                    continue
                cells = [c.strip() for c in row.strip('|').split('|')]
                rows.append({'cells': cells, 'is_header': False})
                i += 1
            if rows:
                paras.append({
                    'style': 'NORMAL_TEXT', 'runs': [],
                    'list': None, 'nesting': 0,
                    'table': rows, 'para_bg': None,
                })
            continue

        # ── Bullet list items ─────────────────────────────────────────────────
        lm = re.match(r'^(\s*)[-*]\s+(.+)', line)
        if lm:
            flush()
            paras.append({
                'style': 'NORMAL_TEXT',
                'runs': _parse_inline(lm.group(2).strip()),
                'list': 'BULLET',
                'nesting': len(lm.group(1)) // 2,
                'table': None, 'para_bg': None,
            })
            i += 1
            continue

        # ── Numbered list items ───────────────────────────────────────────────
        lm = re.match(r'^(\s*)\d+[.)]\s+(.+)', line)
        if lm:
            flush()
            paras.append({
                'style': 'NORMAL_TEXT',
                'runs': _parse_inline(lm.group(2).strip()),
                'list': 'NUMBERED',
                'nesting': len(lm.group(1)) // 2,
                'table': None, 'para_bg': None,
            })
            i += 1
            continue

        # ── Regular paragraph text (accumulate multi-line) ───────────────────
        pending.append(line)
        i += 1

    flush()
    return paras


def _markdown_to_doc_requests(paras, tab_id=None, start_index=1):
    """Convert paragraph dicts to Google Docs batchUpdate request lists.

    Returns (text_requests, format_requests).  Always execute text_requests
    first in a separate batchUpdate call — format_requests reference character
    indices that only exist after all text has been inserted.
    """
    text_reqs, fmt_reqs = [], []
    idx = start_index

    def _loc(i):
        loc = {'index': i}
        if tab_id:
            loc['tabId'] = tab_id
        return loc

    def _rng(s, e):
        r = {'startIndex': s, 'endIndex': e}
        if tab_id:
            r['tabId'] = tab_id
        return r

    def ins(text):
        nonlocal idx
        if not text:
            return idx, idx
        s = idx
        text_reqs.append({'insertText': {'location': _loc(idx), 'text': text}})
        idx += len(text)
        return s, idx

    def set_para_style(s, e, style):
        fmt_reqs.append({
            'updateParagraphStyle': {
                'range': _rng(s, e),
                'paragraphStyle': {'namedStyleType': style},
                'fields': 'namedStyleType',
            }
        })

    def set_para_shading(s, e, bg):
        fmt_reqs.append({
            'updateParagraphStyle': {
                'range': _rng(s, e),
                'paragraphStyle': {
                    'shading': {'backgroundColor': {'color': {'rgbColor': bg}}}
                },
                'fields': 'shading',
            }
        })

    def set_text_style(s, e, bold=None, italic=None, link=None, bg=None, font=None):
        style, fields = {}, []
        if bold   is not None: style['bold']   = bold;   fields.append('bold')
        if italic is not None: style['italic'] = italic; fields.append('italic')
        if link   is not None: style['link'] = {'url': link}; fields.append('link')
        if bg is not None:
            style['backgroundColor'] = {'color': {'rgbColor': bg}}
            fields.append('backgroundColor')
        if font is not None:
            style['weightedFontFamily'] = {'fontFamily': font}
            fields.append('weightedFontFamily')
        if not fields:
            return
        fmt_reqs.append({
            'updateTextStyle': {
                'range': _rng(s, e),
                'textStyle': style,
                'fields': ','.join(fields),
            }
        })

    for para in paras:
        # ── Table: text-based rendering ───────────────────────────────────────
        if para.get('table'):
            for row in para['table']:
                row_text = ' | '.join(row['cells']) + '\n'
                rs, re_ = ins(row_text)
                set_para_style(rs, re_, 'NORMAL_TEXT')
                if row.get('is_header'):
                    set_text_style(rs, re_, bold=True, bg=_BG_TABLE_HEADER)
            continue

        # ── Paragraph with inline runs ────────────────────────────────────────
        runs = para.get('runs', [])
        if not runs:
            ps, pe = ins('\n')
            set_para_style(ps, pe, 'NORMAL_TEXT')
            continue

        para_start = idx
        for run in runs:
            rt = run.get('text', '')
            if not rt:
                continue
            rs, re_ = ins(rt)
            set_text_style(
                rs, re_,
                bold=run.get('bold'),
                italic=run.get('italic'),
                link=run.get('link'),
                bg=run.get('bg_color'),
                font=run.get('font'),
            )
        ins('\n')
        para_end = idx

        set_para_style(para_start, para_end, para['style'])
        if para.get('para_bg'):
            set_para_shading(para_start, para_end, para['para_bg'])

        if para.get('list'):
            preset = (
                'NUMBERED_DECIMAL_ALPHA_ROMAN'
                if para['list'] == 'NUMBERED'
                else 'BULLET_DISC_CIRCLE_SQUARE'
            )
            fmt_reqs.append({
                'createParagraphBullets': {
                    'range': _rng(para_start, para_end),
                    'bulletPreset': preset,
                }
            })
            nesting = para.get('nesting', 0)
            if nesting > 0:
                fmt_reqs.append({
                    'updateParagraphStyle': {
                        'range': _rng(para_start, para_end),
                        'paragraphStyle': {
                            'indentStart': {
                                'magnitude': 18.0 * (nesting + 1),
                                'unit': 'PT',
                            }
                        },
                        'fields': 'indentStart',
                    }
                })

    return text_reqs, fmt_reqs


def _find_or_create_tab(docs_service, doc_id, tab_name):
    """Find a named tab in a Google Doc or create it.

    Returns (tab_id, start_index).  start_index is the character position at
    which new content should be inserted:
      - New tab:      1  (the tab body is empty)
      - Existing tab: position just before the trailing body newline (append)
    """
    doc = docs_service.documents().get(
        documentId=doc_id,
        fields='tabs(tabProperties)',
    ).execute(num_retries=5)

    existing_tabs = doc.get('tabs', [])
    print(f"[DEBUG] Tabs found in doc: {[t.get('tabProperties', {}).get('title') for t in existing_tabs]}")

    for tab in existing_tabs:
        props = tab.get('tabProperties', {})
        if props.get('title') == tab_name:
            tab_id = props['tabId']
            print(f"[DEBUG] Existing tab '{tab_name}' found — id: {tab_id}")
            doc_full = docs_service.documents().get(
                documentId=doc_id,
                includeTabsContent=True,
                fields='tabs(tabProperties,documentTab.body.content)',
            ).execute(num_retries=5)
            for t in doc_full.get('tabs', []):
                if t.get('tabProperties', {}).get('tabId') == tab_id:
                    content = (
                        t.get('documentTab', {})
                         .get('body', {})
                         .get('content', [])
                    )
                    end_idx = content[-1].get('endIndex', 2) if content else 2
                    return tab_id, max(1, end_idx - 1)
            return tab_id, 1

    # Tab not found — create it
    print(f"[DEBUG] Tab '{tab_name}' not found — creating")
    result = docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{'addDocumentTab': {'tabProperties': {'title': tab_name}}}]},
    ).execute(num_retries=5)

    print(f"[DEBUG] addDocumentTab raw reply: {result.get('replies')}")

    new_tab_id = (
        (result.get('replies') or [{}])[0]
        .get('addDocumentTab', {})
        .get('tabProperties', {})
        .get('tabId')
    )
    print(f"[DEBUG] new_tab_id from reply: {new_tab_id!r}")
    if not new_tab_id:
        # Re-read to find the newly created tab
        print("[DEBUG] Falling back to re-read to find new tab")
        doc = docs_service.documents().get(
            documentId=doc_id,
            fields='tabs(tabProperties)',
        ).execute(num_retries=5)
        all_tabs = doc.get('tabs', [])
        print(f"[DEBUG] Tabs after creation: {[t.get('tabProperties', {}).get('title') for t in all_tabs]}")
        for tab in all_tabs:
            if tab.get('tabProperties', {}).get('title') == tab_name:
                new_tab_id = tab['tabProperties']['tabId']
                print(f"[DEBUG] Found new tab by name — id: {new_tab_id!r}")
                break
    if not new_tab_id:
        raise RuntimeError(
            f"createTab succeeded but could not retrieve tabId for '{tab_name}'. "
            "Content was NOT written to avoid polluting the wrong tab."
        )
    return new_tab_id, 1


def _batch_update_doc(docs_service, doc_id, requests, chunk_size=500):
    """Execute Docs batchUpdate requests in sequential chunks of chunk_size."""
    for i in range(0, len(requests), chunk_size):
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests[i:i + chunk_size]},
        ).execute(num_retries=5)


def write_markdown_to_doc(doc_id, file_paths):
    """Write one or more markdown KB files to named tabs in a Google Doc.

    Each file is written to a tab named after the filename (without .md).
    If the tab already exists, new content is appended; otherwise a new tab is
    created.  Intra-KB links are resolved to Zendesk URLs via the product's
    _Metadata/URLs.csv, auto-detected from the file path.

    Args:
        doc_id:     Google Doc ID.
        file_paths: List of paths to .md files (str or Path objects).
    """
    docs_service = get_docs_service()
    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            print(f"[WARN] File not found: {fp} — skipping")
            continue

        tab_name = p.stem
        print(f"Processing '{p.name}' → tab '{tab_name}' …")

        content = p.read_text(encoding='utf-8')
        url_map = _load_kb_url_map(str(p.resolve()))
        content = _preprocess_markdown_links(content, url_map)
        paras = _parse_markdown_to_paras(content)

        tab_id, start_index = _find_or_create_tab(docs_service, doc_id, tab_name)

        text_reqs, fmt_reqs = _markdown_to_doc_requests(
            paras, tab_id=tab_id, start_index=start_index,
        )

        if not text_reqs:
            print(f"  No content generated for '{p.name}' — skipping")
            continue

        _batch_update_doc(docs_service, doc_id, text_reqs)
        if fmt_reqs:
            _batch_update_doc(docs_service, doc_id, fmt_reqs)

        print(f"  Done — {len(text_reqs)} text requests, {len(fmt_reqs)} format requests")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Drive utility')
    subparsers = parser.add_subparsers(dest='command')

    cf = subparsers.add_parser('create-folder', help='Create a folder in Drive')
    cf.add_argument('name', help='Folder name')
    cf.add_argument('--parent', help='Parent folder ID', default=None)

    cd = subparsers.add_parser('create-doc', help='Create a Google Doc in Drive')
    cd.add_argument('name', help='Doc name')
    cd.add_argument('--parent', help='Parent folder ID', default=None)

    cs = subparsers.add_parser('create-sheet', help='Create a Google Sheet in Drive')
    cs.add_argument('name', help='Sheet name')
    cs.add_argument('--parent', help='Parent folder ID', default=None)

    up = subparsers.add_parser('upload', help='Upload a file to Drive')
    up.add_argument('path', help='Local file path')
    up.add_argument('--parent', help='Parent folder ID', default=None)
    up.add_argument('--name', help='Name for the file in Drive', default=None)

    rd = subparsers.add_parser('read-doc', help='Print the plain text of a Google Doc')
    rd.add_argument('doc_id_or_url', help='Google Doc ID or full URL')

    wmd = subparsers.add_parser(
        'write-markdown-to-doc',
        help='Write markdown KB file(s) to named tabs in a Google Doc',
    )
    wmd.add_argument('doc_id', help='Google Doc ID')
    wmd.add_argument(
        '--files', nargs='+', required=True, metavar='FILE',
        help='One or more paths to .md files',
    )

    args = parser.parse_args()

    if args.command == 'create-folder':
        create_folder(args.name, args.parent)
    elif args.command == 'create-doc':
        create_doc(args.name, args.parent)
    elif args.command == 'create-sheet':
        create_sheet(args.name, args.parent)
    elif args.command == 'upload':
        upload_file(args.path, args.parent, args.name)
    elif args.command == 'read-doc':
        raw = args.doc_id_or_url
        if '/d/' in raw:
            doc_id = raw.split('/d/')[1].split('/')[0]
        else:
            doc_id = raw
        print(read_doc(doc_id))
    elif args.command == 'write-markdown-to-doc':
        write_markdown_to_doc(args.doc_id, args.files)
    else:
        parser.print_help()


# NOTE: Run all scripts with `python -B drive.py ...` to suppress __pycache__ creation.

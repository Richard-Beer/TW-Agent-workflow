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
  python -B drive.py apply-drafts "<doc_id>" --kb-path "<path_to_kb_repo_root>"

Use append_rows() in scripts (not the Sheets API append directly) to add data rows without
inheriting header formatting. See append_rows() docstring for details.

Use draft_rows() in temp scripts to write drafts into specific cells of an existing sheet.
Pass a list of (A1-notation range, value) tuples — e.g. [('Sheet1!D2', 'My text'), ...].

Run setup_auth.py first to authenticate.
The -B flag suppresses __pycache__ creation.
"""

import argparse
import os
import pickle

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from microcopy_scope import (
    MICROCOPY_HEADERS,
    HEADER_ROW_HEIGHT,
    CELL_TEXT_FORMAT,
    CELL_VERTICAL_ALIGNMENT,
    CELL_HORIZONTAL_ALIGNMENT,
    CELL_WRAP_STRATEGY,
)

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'token.pickle')


def _get_creds():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'wb') as f:
                pickle.dump(creds, f)
        else:
            raise RuntimeError("No valid credentials found. Run setup_auth.py first.")
    return creds


def get_service():
    return build('drive', 'v3', credentials=_get_creds())


def get_sheets_service():
    return build('sheets', 'v4', credentials=_get_creds())


def create_folder(name, parent_id=None):
    """Create a folder in Drive. Returns the folder ID."""
    service = get_service()
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        metadata['parents'] = [parent_id]
    folder = service.files().create(body=metadata, fields='id, name').execute()
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
    doc = service.files().create(body=metadata, fields='id, name').execute()
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
    sheet = service.files().create(body=metadata, fields='id, name').execute()
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

    get_sheets_service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': requests},
    ).execute()

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
    ).execute()

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
        ).execute()
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
    ).execute()
    print(f"Updated {result.get('totalUpdatedCells', 0)} cells")


def get_docs_service():
    return build('docs', 'v1', credentials=_get_creds())


def _parse_markdown_table(content):
    """Parse a markdown table into a list of rows, each a list of cell strings.

    Strips the separator row (e.g. |---|---|---|).
    """
    import re
    # Strip BOM if present
    content = content.lstrip('\ufeff')
    rows = []
    for line in content.strip().splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        # Skip separator rows
        if re.match(r'^\|[\s\-:|]+\|$', line):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        rows.append(cells)
    return rows


def _parse_cell_segments(text):
    """Parse a cell's markdown into segments for Google Docs formatting.

    Returns a list of dicts: {'text': str, 'bold': bool, 'url': str or None}
    """
    import re
    segments = []
    # Pattern matches **bold**, [link](url), or plain text
    pattern = r'(\*\*(.+?)\*\*)|(\[([^\]]+)\]\(([^)]+)\))'
    last_end = 0
    for m in re.finditer(pattern, text):
        # Plain text before this match
        if m.start() > last_end:
            plain = text[last_end:m.start()]
            if plain:
                segments.append({'text': plain, 'bold': False, 'url': None})
        if m.group(1):  # bold
            segments.append({'text': m.group(2), 'bold': True, 'url': None})
        elif m.group(3):  # link
            segments.append({'text': m.group(4), 'bold': False, 'url': m.group(5)})
        last_end = m.end()
    # Trailing plain text
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            segments.append({'text': remaining, 'bold': False, 'url': None})
    # If no segments found, treat entire text as plain
    if not segments and text:
        segments.append({'text': text, 'bold': False, 'url': None})
    return segments


def write_doc_scope(doc_id, content):
    """Write scope content to a Google Doc as a native table with formatting.

    Parses the markdown table, clears existing doc content, inserts a Google Docs
    table, and applies formatting:
    - Header row (row 0): bold text with grey background
    - Inline bold and hyperlink formatting preserved

    Args:
        doc_id:  Google Docs file ID.
        content: Markdown table string.
    """
    svc = get_docs_service()

    # Parse markdown into rows
    rows = _parse_markdown_table(content)
    if not rows:
        print("No table rows found in content.")
        return

    num_rows = len(rows)
    num_cols = len(rows[0])

    # Step 1: Clear existing content and insert table
    doc = svc.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])
    end_index = 1
    for element in body_content:
        if 'endIndex' in element:
            end_index = element['endIndex']

    init_requests = []
    if end_index > 2:
        init_requests.append({
            'deleteContentRange': {
                'range': {'startIndex': 1, 'endIndex': end_index - 1}
            }
        })
    # Insert heading text, then style it, then insert the table after it
    heading_text = 'Scope\n'
    init_requests.append({
        'insertText': {
            'location': {'index': 1},
            'text': heading_text,
        }
    })
    init_requests.append({
        'updateParagraphStyle': {
            'range': {'startIndex': 1, 'endIndex': 1 + len(heading_text)},
            'paragraphStyle': {'namedStyleType': 'HEADING_1'},
            'fields': 'namedStyleType',
        }
    })
    init_requests.append({
        'insertTable': {
            'location': {'index': 1 + len(heading_text)},
            'rows': num_rows,
            'columns': num_cols,
        }
    })
    svc.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': init_requests},
    ).execute()

    # Step 2: Read doc to find cell indices
    doc = svc.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])

    table = None
    table_start_index = None
    for element in body_content:
        if 'table' in element:
            table = element['table']
            table_start_index = element.get('startIndex', 1)
            break

    if not table:
        print("Error: table not found in document after insertion.")
        return

    # Step 3: Insert text into cells (work backwards to preserve indices)
    text_requests = []
    for row_idx in range(num_rows - 1, -1, -1):
        table_row = table['tableRows'][row_idx]
        doc_cells = table_row['tableCells']
        for col_idx in range(num_cols - 1, -1, -1):
            if col_idx >= len(doc_cells) or col_idx >= len(rows[row_idx]):
                continue
            cell_text = rows[row_idx][col_idx]
            if not cell_text:
                continue
            segments = _parse_cell_segments(cell_text)
            full_text = ''.join(seg['text'] for seg in segments)
            cell_start = doc_cells[col_idx]['content'][0]['paragraph']['elements'][0]['startIndex']
            text_requests.append({
                'insertText': {
                    'location': {'index': cell_start},
                    'text': full_text,
                }
            })

    if text_requests:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': text_requests},
        ).execute()

    # Step 4: Re-read doc and apply formatting
    doc = svc.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])
    table = None
    table_start_index = None
    for element in body_content:
        if 'table' in element:
            table = element['table']
            table_start_index = element.get('startIndex', 1)
            break

    if not table:
        return

    fmt_requests = []
    for row_idx in range(num_rows):
        table_row = table['tableRows'][row_idx]
        doc_cells = table_row['tableCells']

        if row_idx == 0:
            # Header row — bold all text + grey background on each cell
            for col_idx in range(min(num_cols, len(doc_cells))):
                cell = doc_cells[col_idx]
                cell_start = cell['content'][0]['paragraph']['elements'][0]['startIndex']
                cell_text = rows[row_idx][col_idx] if col_idx < len(rows[row_idx]) else ''
                if cell_text:
                    full_text = ''.join(seg['text'] for seg in _parse_cell_segments(cell_text))
                    if full_text:
                        fmt_requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': cell_start, 'endIndex': cell_start + len(full_text)},
                                'textStyle': {'bold': True},
                                'fields': 'bold',
                            }
                        })
                fmt_requests.append({
                    'updateTableCellStyle': {
                        'tableCellStyle': {
                            'backgroundColor': {'color': {'rgbColor': _BG_TABLE_HEADER}},
                        },
                        'tableRange': {
                            'tableCellLocation': {
                                'tableStartLocation': {'index': table_start_index},
                                'rowIndex': 0,
                                'columnIndex': col_idx,
                            },
                            'rowSpan': 1,
                            'columnSpan': 1,
                        },
                        'fields': 'backgroundColor',
                    }
                })
        else:
            # Data rows — apply inline bold/link formatting
            for col_idx in range(min(num_cols, len(doc_cells))):
                if col_idx >= len(rows[row_idx]):
                    continue
                cell_text = rows[row_idx][col_idx]
                if not cell_text:
                    continue
                cell = doc_cells[col_idx]
                cell_start = cell['content'][0]['paragraph']['elements'][0]['startIndex']
                segments = _parse_cell_segments(cell_text)
                offset = cell_start
                for seg in segments:
                    seg_len = len(seg['text'])
                    if seg['bold']:
                        fmt_requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': offset, 'endIndex': offset + seg_len},
                                'textStyle': {'bold': True},
                                'fields': 'bold',
                            }
                        })
                    if seg['url']:
                        fmt_requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': offset, 'endIndex': offset + seg_len},
                                'textStyle': {'link': {'url': seg['url']}},
                                'fields': 'link',
                            }
                        })
                    offset += seg_len

    if fmt_requests:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': fmt_requests},
        ).execute()

    # Rename the first tab to "Scope"
    doc = svc.documents().get(documentId=doc_id, includeTabsContent=True).execute()
    tabs = doc.get('tabs', [])
    if tabs:
        tab_id = tabs[0].get('tabProperties', {}).get('tabId', '')
        if tab_id:
            svc.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': [{
                    'updateDocumentTabProperties': {
                        'tabProperties': {
                            'tabId': tab_id,
                            'title': 'Scope',
                        },
                        'fields': 'title',
                    }
                }]},
            ).execute()

    print(f"Wrote scope table ({num_rows} rows x {num_cols} cols) to doc {doc_id}")
    return rows


def _get_scope_articles(rows):
    """Extract primary and secondary update articles from parsed scope table rows.

    Returns a list of dicts: {'name': str, 'action': str, 'url': str or None}
    Includes rows from both 'Primary updates' and 'Secondary updates' sections.
    """
    import re
    articles = []
    in_section = False
    for row in rows:
        if not row:
            continue
        first_cell = row[0]
        # Detect section headers
        if 'Primary updates' in first_cell or 'Secondary updates' in first_cell:
            in_section = True
            continue
        if not in_section:
            continue
        # Parse article name and URL from link markdown
        link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', first_cell)
        if link_match:
            name = link_match.group(1)
            url = link_match.group(2)
        else:
            name = re.sub(r'\*\*', '', first_cell).strip()
            url = None
        action = row[1].strip() if len(row) > 1 else ''
        if name and action:
            articles.append({'name': name, 'action': action, 'url': url})
    return articles


def _load_variables(kb_root):
    """Load MadCap Flare variables from .flvar files in the project.

    Args:
        kb_root: Root of the knowledge base repo (e.g. 'Cin7 Omni knowledge base/').

    Returns a dict mapping 'SetName.VarName' → value string.
    """
    import xml.etree.ElementTree as ET
    import glob as _glob

    variables = {}
    var_dir = os.path.join(kb_root, 'Project', 'VariableSets')
    if not os.path.isdir(var_dir):
        return variables

    for flvar_path in _glob.glob(os.path.join(var_dir, '*.flvar')):
        set_name = os.path.splitext(os.path.basename(flvar_path))[0]
        try:
            tree = ET.parse(flvar_path)
            root = tree.getroot()
            for var_el in root.findall('Variable'):
                var_name = var_el.get('Name', '')
                var_value = var_el.text or var_el.get('EvaluatedDefinition', '')
                if var_name:
                    variables[f"{set_name}.{var_name}"] = var_value
        except ET.ParseError:
            pass
    return variables


def _load_url_map(kb_root):
    """Load filename→Zendesk URL mapping from the topics.csv in the KB repo.

    The CSV lives at .github/zendesk-mappings/output/topics.csv with columns:
    filename, h1_title, zendesk_title, url, status.

    Returns a dict mapping lowercase filename (without extension) → URL.
    Only 'matched' rows with a non-empty URL are included.
    """
    import csv as _csv

    url_map = {}
    csv_path = os.path.join(kb_root, '.github', 'zendesk-mappings', 'output', 'topics.csv')
    if not os.path.isfile(csv_path):
        print(f"  URL map not found: {csv_path}")
        return url_map

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = _csv.DictReader(f)
        for row in reader:
            filename = row.get('filename', '').strip()
            url = row.get('url', '').strip()
            if filename and url:
                url_map[filename.lower()] = url

    print(f"  Loaded {len(url_map)} URL mappings from {csv_path}")
    return url_map


def _resolve_href(href, url_map):
    """Resolve a local .htm href to a Zendesk URL using the mapping.

    If href is already an absolute URL (http/https), return as-is.
    If it's a local .htm reference, look up the filename (without extension)
    in url_map and return the Zendesk URL. Returns the original href if
    no match is found.
    """
    if not href:
        return href
    if href.startswith(('http://', 'https://', 'mailto:')):
        return href

    # Strip fragment and query
    clean = href.split('#')[0].split('?')[0]
    # Get just the filename without path or extension
    basename = os.path.basename(clean)
    if basename.lower().endswith('.htm'):
        basename = basename[:-4]
    elif basename.lower().endswith('.html'):
        basename = basename[:-5]
    else:
        return href

    return url_map.get(basename.lower(), href)


def _resolve_snippet(src_path, topics_dir, variables):
    """Read a .flsnp snippet file and return its body HTML content.

    Resolves variables inside the snippet. Strips the outer <html>/<body> wrapper.

    Args:
        src_path:   The src attribute value (e.g. '../Snippets/Foo.flsnp').
        topics_dir: Absolute path to the Topics directory containing the .htm file.
        variables:  Dict of variable name → value.

    Returns the inner body HTML as a string, or '' if not found.
    """
    import re

    # Resolve the path relative to the topics dir
    abs_path = os.path.normpath(os.path.join(topics_dir, src_path))
    if not os.path.isfile(abs_path):
        return ''

    with open(abs_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Extract body content
    body_match = re.search(r'<body[^>]*>(.*?)</body>', raw, re.DOTALL)
    if body_match:
        body_html = body_match.group(1).strip()
    else:
        body_html = raw

    # Resolve variables within snippet
    body_html = _substitute_variables(body_html, variables)

    return body_html


def _substitute_variables(html, variables):
    """Replace <MadCap:variable name="X.Y" /> tags with their values."""
    import re

    def _var_repl(m):
        name = m.group(1)
        return variables.get(name, name)

    # Match both self-closing and open/close forms
    html = re.sub(
        r'<MadCap:variable\s+name="([^"]+)"[^/>]*/\s*>',
        _var_repl, html)
    html = re.sub(
        r'<MadCap:variable\s+name="([^"]+)"[^>]*>.*?</MadCap:variable>',
        _var_repl, html)
    return html


# Background colours for special content in Google Docs (RGB 0-1 floats)
_BG_OVERVIEW = {'red': 0.85, 'green': 0.92, 'blue': 1.0}   # light blue
_BG_NOTE     = {'red': 1.0,  'green': 0.95, 'blue': 0.8}    # light amber
_BG_WARNING  = {'red': 1.0,  'green': 0.87, 'blue': 0.87}   # light red
_BG_SNIPPET  = {'red': 0.9,  'green': 0.96, 'blue': 0.9}    # light green
_BG_VARIABLE = {'red': 0.95, 'green': 0.9,  'blue': 1.0}    # light purple
_BG_IMAGE    = {'red': 1.0,  'green': 1.0,  'blue': 0.0}    # bright yellow


def _htm_to_doc_requests(html_content, topics_dir, variables, start_index=1, url_map=None):
    """Convert a MadCap Flare .htm file body to Google Docs API requests.

    Handles:
    - Snippet inlining (with green background)
    - Variable substitution (with purple background highlight)
    - Overview divs (blue background)
    - Note paragraphs (amber background)
    - Warning divs (red background)
    - Standard HTML: headings, paragraphs, bold, italic, links, lists, tables
    - Images are stripped (not included in output)

    Args:
        html_content: Raw HTML string from the .htm file body.
        topics_dir:   Absolute path to the Topics directory.
        variables:    Dict of variable name → value.
        start_index:  Document index to start inserting at.
        url_map:      Dict mapping lowercase filename (no ext) → Zendesk URL.
                      Local .htm hrefs are resolved to Zendesk URLs using this map.

    Returns (text_requests, format_requests) for the Google Docs API.
    """
    import re
    from html.parser import HTMLParser

    # --- Pre-processing: resolve snippets and mark their boundaries ---
    # Wrap snippet content with markers so we can apply background colours later
    def _snippet_block_repl(m):
        src = m.group(1)
        content = _resolve_snippet(src, topics_dir, variables)
        if content:
            return f'<!-- snippet:start -->{content}<!-- snippet:end -->'
        return ''

    def _snippet_text_repl(m):
        src = m.group(1)
        content = _resolve_snippet(src, topics_dir, variables)
        if content:
            content = re.sub(r'^\s*<p[^>]*>(.*?)</p>\s*$', r'\1', content, flags=re.DOTALL)
            return f'<!-- snippet:start -->{content}<!-- snippet:end -->'
        return ''

    processed = re.sub(
        r'<MadCap:snippetBlock\s+src="([^"]+)"\s*/\s*>',
        _snippet_block_repl, html_content)
    processed = re.sub(
        r'<MadCap:snippetText\s+src="([^"]+)"\s*/\s*>',
        _snippet_text_repl, processed)

    # Mark variable positions with comment markers for background colouring
    def _var_mark(m):
        name = m.group(1)
        val = variables.get(name, name)
        return f'<!-- var:start -->{val}<!-- var:end -->'

    processed = re.sub(
        r'<MadCap:variable\s+name="([^"]+)"[^/>]*/\s*>',
        _var_mark, processed)
    processed = re.sub(
        r'<MadCap:variable\s+name="([^"]+)"[^>]*>.*?</MadCap:variable>',
        _var_mark, processed)

    # Replace image tags with highlighted placeholders
    def _img_placeholder(m):
        tag = m.group(0)
        src_match = re.search(r'src="([^"]+)"', tag)
        path = src_match.group(1) if src_match else 'unknown'
        return f'<!-- img:start -->[Image: {path}]<!-- img:end -->'

    processed = re.sub(r'<img[^>]*/?>', _img_placeholder, processed)

    # Strip MadCap conditions/other unsupported MadCap tags
    processed = re.sub(r'<MadCap:[^>]*/?>', '', processed)
    processed = re.sub(r'<MadCap:[^>]*>.*?</MadCap:[^>]+>', '', processed, flags=re.DOTALL)

    # --- Parse the pre-processed HTML ---
    class HtmDocsBuilder(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = ''
            self.formats = []
            self.tag_stack = []
            self.link_stack = []
            self.list_stack = []
            self.li_stack = []  # stack of {'start': int, 'depth': int, 'child_list_start': int or None}
            self.list_ranges = []  # completed top-level lists: {'start', 'end', 'preset'}
            self.top_list_start = None  # text position where the outermost list began

            # Track special regions
            self.region_stack = []  # list of {'type': str, 'start': int}
            self.regions = []      # completed regions: {'type', 'start', 'end'}

            # Table handling
            self.in_table = False
            self.table_rows = []
            self.current_row = []
            self.current_cell = ''
            self.current_cell_formats = []
            self.cell_is_header = False
            self.skip_content = False

        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            tag = tag.lower()

            if tag in ('script', 'style', 'head'):
                self.skip_content = True
                return

            if self.skip_content:
                return

            # Detect special div/p classes
            css_class = attrs_dict.get('class', '')
            if tag == 'div' and 'overview' in css_class:
                self.region_stack.append({'type': 'overview', 'start': len(self.text)})
            elif tag == 'div' and 'warning' in css_class:
                self.region_stack.append({'type': 'warning', 'start': len(self.text)})
            elif tag == 'div' and 'note' in css_class:
                self.region_stack.append({'type': 'note', 'start': len(self.text)})
            elif tag == 'p' and 'note' in css_class:
                self.region_stack.append({'type': 'note', 'start': len(self.text)})

            if tag == 'table':
                self.in_table = True
                self.table_rows = []
                return

            if self.in_table:
                if tag == 'tr':
                    self.current_row = []
                    self.row_is_subheader = ('subheader' in css_class)
                elif tag in ('td', 'th'):
                    self.current_cell = ''
                    self.current_cell_formats = []
                    self.cell_is_header = (tag == 'th')
                    self.cell_colspan = int(attrs_dict.get('colspan', 1))
                    self.cell_rowspan = int(attrs_dict.get('rowspan', 1))
                elif tag in ('strong', 'b'):
                    self.current_cell_formats.append(('bold_start', len(self.current_cell)))
                elif tag in ('em', 'i'):
                    self.current_cell_formats.append(('italic_start', len(self.current_cell)))
                elif tag == 'a':
                    href = attrs_dict.get('href', '')
                    href = _resolve_href(href, url_map or {})
                    self.current_cell_formats.append(('link_start', len(self.current_cell), href))
                elif tag == 'br':
                    self.current_cell += '\v'
                return

            self.tag_stack.append(tag)

            if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                if self.text and not self.text.endswith('\n'):
                    self.text += '\n'
            elif tag == 'p':
                if self.text and not self.text.endswith('\n'):
                    self.text += '\n'
            elif tag == 'br':
                self.text += '\v'
            elif tag in ('ul', 'ol'):
                ol_type = attrs_dict.get('type', '1') if tag == 'ol' else None
                self.list_stack.append((tag, ol_type))
                # Record start of the outermost list
                if len(self.list_stack) == 1:
                    self.top_list_start = len(self.text)
                # Mark that the current parent li has a child list
                if self.li_stack and self.li_stack[-1]['child_list_start'] is None:
                    self.li_stack[-1]['child_list_start'] = len(self.text)
            elif tag == 'li':
                if self.text and not self.text.endswith('\n'):
                    self.text += '\n'
                self.li_stack.append({
                    'start': len(self.text),
                    'depth': len(self.list_stack) - 1,
                    'child_list_start': None,
                })
            elif tag in ('strong', 'b'):
                self.formats.append({'type': 'bold_start', 'pos': len(self.text)})
            elif tag in ('em', 'i'):
                self.formats.append({'type': 'italic_start', 'pos': len(self.text)})
            elif tag == 'a':
                href = attrs_dict.get('href', '')
                href = _resolve_href(href, url_map or {})
                self.link_stack.append({'start': len(self.text), 'url': href})
            elif tag == 'blockquote':
                if self.text and not self.text.endswith('\n'):
                    self.text += '\n'

        def handle_endtag(self, tag):
            tag = tag.lower()

            if tag in ('script', 'style', 'head'):
                self.skip_content = False
                return

            if self.skip_content:
                return

            # Close special regions
            css_class_tag = tag
            if css_class_tag == 'div':
                for i in range(len(self.region_stack) - 1, -1, -1):
                    if self.region_stack[i]['type'] in ('overview', 'warning', 'note'):
                        region = self.region_stack.pop(i)
                        region['end'] = len(self.text)
                        self.regions.append(region)
                        break
            elif css_class_tag == 'p':
                for i in range(len(self.region_stack) - 1, -1, -1):
                    if self.region_stack[i]['type'] == 'note':
                        region = self.region_stack.pop(i)
                        region['end'] = len(self.text)
                        self.regions.append(region)
                        break

            if tag == 'table':
                self.in_table = False
                self._flush_table()
                return

            if self.in_table:
                if tag in ('td', 'th'):
                    self.current_row.append({
                        'text': self.current_cell,
                        'formats': self.current_cell_formats,
                        'is_header': self.cell_is_header,
                        'is_subheader': getattr(self, 'row_is_subheader', False),
                        'colspan': getattr(self, 'cell_colspan', 1),
                        'rowspan': getattr(self, 'cell_rowspan', 1),
                    })
                elif tag == 'tr':
                    self.table_rows.append(self.current_row)
                elif tag in ('strong', 'b'):
                    self.current_cell_formats.append(('bold_end', len(self.current_cell)))
                elif tag in ('em', 'i'):
                    self.current_cell_formats.append(('italic_end', len(self.current_cell)))
                elif tag == 'a':
                    self.current_cell_formats.append(('link_end', len(self.current_cell)))
                elif tag == 'p':
                    if self.current_cell and not self.current_cell.endswith('\n'):
                        self.current_cell += '\n'
                return

            if tag in self.tag_stack:
                self.tag_stack.remove(tag)

            if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                level = int(tag[1])
                heading_start = self.text.rfind('\n', 0, len(self.text)) + 1
                self.text += '\n'
                self.formats.append({
                    'type': 'heading',
                    'level': level,
                    'start': heading_start,
                    'end': len(self.text),
                })
            elif tag == 'p':
                self.text += '\n'
            elif tag in ('ul', 'ol'):
                if self.list_stack:
                    popped_tag, popped_ol_type = self.list_stack.pop()
                    # When the outermost list closes, record the full range
                    if not self.list_stack and self.top_list_start is not None:
                        list_end = len(self.text)
                        if popped_tag == 'ul':
                            preset = 'BULLET_DISC_CIRCLE_SQUARE'
                        else:
                            preset_map = {
                                '1': 'NUMBERED_DECIMAL_ALPHA_ROMAN',
                                'a': 'NUMBERED_ALPHA_ROMAN_DECIMAL',
                                'A': 'NUMBERED_UPPERALPHA_ALPHA_ROMAN',
                                'i': 'NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL',
                                'I': 'NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL',
                            }
                            preset = preset_map.get(popped_ol_type, 'NUMBERED_DECIMAL_ALPHA_ROMAN')
                        self.list_ranges.append({
                            'start': self.top_list_start,
                            'end': list_end,
                            'preset': preset,
                        })
                        self.top_list_start = None
            elif tag == 'li':
                li_end = len(self.text)
                if not self.text.endswith('\n'):
                    self.text += '\n'
                    li_end = len(self.text)

                li_info = self.li_stack.pop() if self.li_stack else None
                if li_info:
                    li_start = li_info['start']
                    depth = li_info['depth']
                else:
                    li_start = self.text.rfind('\n', 0, li_end - 1)
                    li_start = 0 if li_start == -1 else li_start + 1
                    depth = 0

                # Emit indent entry for nested items so createParagraphBullets
                # (applied later) reads the indentation to set nesting level.
                if depth > 0:
                    self.formats.append({
                        'type': 'list_indent',
                        'start': li_start,
                        'end': li_end,
                        'depth': depth,
                    })
            elif tag in ('strong', 'b'):
                for i in range(len(self.formats) - 1, -1, -1):
                    if self.formats[i].get('type') == 'bold_start':
                        self.formats[i] = {
                            'type': 'bold',
                            'start': self.formats[i]['pos'],
                            'end': len(self.text),
                        }
                        break
            elif tag in ('em', 'i'):
                for i in range(len(self.formats) - 1, -1, -1):
                    if self.formats[i].get('type') == 'italic_start':
                        self.formats[i] = {
                            'type': 'italic',
                            'start': self.formats[i]['pos'],
                            'end': len(self.text),
                        }
                        break
            elif tag == 'a':
                if self.link_stack:
                    link_info = self.link_stack.pop()
                    if link_info['url']:
                        self.formats.append({
                            'type': 'link',
                            'start': link_info['start'],
                            'end': len(self.text),
                            'url': link_info['url'],
                        })

        def handle_data(self, data):
            if self.skip_content:
                return
            if self.in_table:
                import re as _re
                data = _re.sub(r'[ \t\n]+', ' ', data)
                if data == ' ' and (not self.current_cell or self.current_cell.endswith('\n')):
                    return
                self.current_cell += data
                return
            import re as _re
            data = _re.sub(r'[ \t\n]+', ' ', data)
            if data == ' ' and (not self.text or self.text.endswith('\n')):
                return
            self.text += data

        def handle_entityref(self, name):
            if self.skip_content:
                return
            import html as _html
            char = _html.unescape(f'&{name};')
            if self.in_table:
                self.current_cell += char
            else:
                self.text += char

        def handle_charref(self, name):
            if self.skip_content:
                return
            import html as _html
            char = _html.unescape(f'&#{name};')
            if self.in_table:
                self.current_cell += char
            else:
                self.text += char

        def handle_comment(self, data):
            """Handle snippet and variable markers from pre-processing."""
            data = data.strip()
            if data == 'snippet:start':
                self.region_stack.append({'type': 'snippet', 'start': len(self.text)})
            elif data == 'snippet:end':
                for i in range(len(self.region_stack) - 1, -1, -1):
                    if self.region_stack[i]['type'] == 'snippet':
                        region = self.region_stack.pop(i)
                        region['end'] = len(self.text)
                        self.regions.append(region)
                        break
            elif data == 'var:start':
                self.region_stack.append({'type': 'variable', 'start': len(self.text)})
            elif data == 'var:end':
                for i in range(len(self.region_stack) - 1, -1, -1):
                    if self.region_stack[i]['type'] == 'variable':
                        region = self.region_stack.pop(i)
                        region['end'] = len(self.text)
                        self.regions.append(region)
                        break
            elif data == 'img:start':
                self.region_stack.append({'type': 'image', 'start': len(self.text)})
            elif data == 'img:end':
                for i in range(len(self.region_stack) - 1, -1, -1):
                    if self.region_stack[i]['type'] == 'image':
                        region = self.region_stack.pop(i)
                        region['end'] = len(self.text)
                        self.regions.append(region)
                        break

        def _flush_table(self):
            if not self.table_rows:
                return
            if self.text and not self.text.endswith('\n'):
                self.text += '\n'
            # Calculate the actual grid width accounting for colspan
            num_cols = 0
            for row in self.table_rows:
                row_span_sum = sum(cell.get('colspan', 1) for cell in row)
                if row_span_sum > num_cols:
                    num_cols = row_span_sum
            self.formats.append({
                'type': 'table',
                'start': len(self.text),
                'rows': self.table_rows,
                'num_rows': len(self.table_rows),
                'num_cols': num_cols,
            })

    builder = HtmDocsBuilder()
    builder.feed(processed)

    full_text = builder.text
    formats = builder.formats
    regions = builder.regions
    list_ranges = builder.list_ranges

    # Separate table formats from inline formats
    tables = [f for f in formats if f.get('type') == 'table']
    inline_formats = [f for f in formats if f.get('type') != 'table']

    text_requests = []
    format_requests = []
    list_bullet_requests = []  # applied last — tab removal shifts indices

    if full_text:
        text_requests.append({
            'insertText': {
                'location': {'index': start_index},
                'text': full_text,
            }
        })

    # List formatting: set indentation on nested items FIRST, then apply
    # createParagraphBullets over the full range.  createParagraphBullets reads
    # existing indentStart to determine each paragraph's nesting level.
    for lr in list_ranges:
        abs_start = start_index + lr['start']
        abs_end = start_index + lr['end']
        if abs_start >= abs_end:
            continue
        list_bullet_requests.append({
            'createParagraphBullets': {
                'range': {'startIndex': abs_start, 'endIndex': abs_end},
                'bulletPreset': lr['preset'],
            }
        })

    # Inline formatting (headings, bold, italic, list indentation)
    for fmt in inline_formats:
        if 'start' not in fmt or 'end' not in fmt:
            continue
        abs_start = start_index + fmt['start']
        abs_end = start_index + fmt['end']
        if abs_start >= abs_end:
            continue

        if fmt['type'] == 'heading':
            level = fmt['level']
            format_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': abs_start, 'endIndex': abs_end},
                    'paragraphStyle': {'namedStyleType': f'HEADING_{min(level, 6)}'},
                    'fields': 'namedStyleType',
                }
            })
        elif fmt['type'] == 'list_indent':
            depth = fmt.get('depth', 1)
            indent = 36 * depth  # 36pt per nesting level
            format_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': abs_start, 'endIndex': abs_end},
                    'paragraphStyle': {
                        'indentStart': {'magnitude': indent, 'unit': 'PT'},
                        'indentFirstLine': {'magnitude': indent, 'unit': 'PT'},
                    },
                    'fields': 'indentStart,indentFirstLine',
                }
            })
        elif fmt['type'] == 'bold':
            format_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': abs_start, 'endIndex': abs_end},
                    'textStyle': {'bold': True},
                    'fields': 'bold',
                }
            })
        elif fmt['type'] == 'italic':
            format_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': abs_start, 'endIndex': abs_end},
                    'textStyle': {'italic': True},
                    'fields': 'italic',
                }
            })
        elif fmt['type'] == 'link':
            format_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': abs_start, 'endIndex': abs_end},
                    'textStyle': {'link': {'url': fmt['url']}},
                    'fields': 'link',
                }
            })

    # Background colour shading for special regions
    _BG_MAP = {
        'overview': _BG_OVERVIEW,
        'note':     _BG_NOTE,
        'warning':  _BG_WARNING,
        'snippet':  _BG_SNIPPET,
        'variable': _BG_VARIABLE,
        'image':    _BG_IMAGE,
    }
    for region in regions:
        abs_start = start_index + region['start']
        abs_end = start_index + region['end']
        if abs_start >= abs_end:
            continue
        bg = _BG_MAP.get(region['type'])
        if not bg:
            continue

        if region['type'] in ('variable', 'image'):
            # Inline highlight: colour the text itself
            format_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': abs_start, 'endIndex': abs_end},
                    'textStyle': {'backgroundColor': {'color': {'rgbColor': bg}}},
                    'fields': 'backgroundColor',
                }
            })
        else:
            # Block regions: shade the paragraph background
            format_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': abs_start, 'endIndex': abs_end},
                    'paragraphStyle': {'shading': {'backgroundColor': {'color': {'rgbColor': bg}}}},
                    'fields': 'shading.backgroundColor',
                }
            })

    # Tables handled separately
    if tables:
        for tbl in tables:
            format_requests.append({
                '_table': True,
                'insert_after_index': start_index + tbl['start'],
                'rows': tbl['rows'],
                'num_rows': tbl['num_rows'],
                'num_cols': tbl['num_cols'],
            })

    # List bullets applied last — createParagraphBullets reads existing
    # indentStart to assign nesting levels, so indent must be set first.
    format_requests.extend(list_bullet_requests)

    return text_requests, format_requests


def _truncate_tab_name(prefix, name, max_len=50):
    """Build a tab name with prefix, truncating the name if needed.

    Google Docs tab names have a max length of 50 characters.
    """
    full = f"{prefix} {name}"
    if len(full) <= max_len:
        return full
    # Truncate the name portion to fit
    available = max_len - len(prefix) - 1  # 1 for the space
    return f"{prefix} {name[:available]}"


_BG_TABLE_HEADER = {'red': 0.85, 'green': 0.85, 'blue': 0.85}  # light grey
_BG_TABLE_SUBHEADER = {'red': 0.94, 'green': 0.97, 'blue': 1.0}  # alice blue (#f0f8ff)


def _find_table_in_tab(svc, doc_id, tab_id, insert_index):
    """Re-read the doc and return (target_tab, table_element) nearest insert_index."""
    doc = svc.documents().get(documentId=doc_id, includeTabsContent=True).execute()
    target_tab = None
    for tab in doc.get('tabs', []):
        if tab.get('tabProperties', {}).get('tabId') == tab_id:
            target_tab = tab
            break
    if not target_tab:
        return None, None
    body_content = target_tab.get('documentTab', {}).get('body', {}).get('content', [])
    table_element = None
    best_distance = float('inf')
    for element in body_content:
        if 'table' in element:
            el_start = element.get('startIndex', 0)
            distance = abs(el_start - insert_index)
            if distance < best_distance:
                best_distance = distance
                table_element = element['table']
    return target_tab, table_element


def _build_merge_grid(rows_data, num_rows, num_cols):
    """Build a grid mapping each (row, grid_col) to its source cell.

    Returns:
        grid: list of rows, each a list of num_cols entries.
              Each entry is (src_row, src_col, cell_data) or None for spanned-over cells.
        merges: list of dicts {'row', 'col', 'rowspan', 'colspan'} for cells that span.
    """
    grid = [[None] * num_cols for _ in range(num_rows)]
    merges = []

    for row_idx, row in enumerate(rows_data):
        grid_col = 0
        for cell_idx, cell_data in enumerate(row):
            # Skip columns already occupied by a previous rowspan
            while grid_col < num_cols and grid[row_idx][grid_col] is not None:
                grid_col += 1
            if grid_col >= num_cols:
                break

            cs = cell_data.get('colspan', 1)
            rs = cell_data.get('rowspan', 1)

            # Fill the grid — reuse the same tuple object so that
            # identity checks (``is``) can detect colspan/rowspan continuations.
            cell_entry = (row_idx, cell_idx, cell_data)
            for dr in range(rs):
                for dc in range(cs):
                    r, c = row_idx + dr, grid_col + dc
                    if r < num_rows and c < num_cols:
                        grid[r][c] = cell_entry

            if cs > 1 or rs > 1:
                merges.append({
                    'row': row_idx,
                    'col': grid_col,
                    'rowspan': rs,
                    'colspan': cs,
                })

            grid_col += cs

    return grid, merges


def _insert_table_in_tab(svc, doc_id, tab_id, table_data):
    """Insert a native Google Docs table into a specific tab.

    Handles cell merging (colspan/rowspan), bold header text, and
    header-row background colouring.

    Args:
        svc:        Google Docs service.
        doc_id:     Document ID.
        tab_id:     Tab ID to insert into.
        table_data: Dict with 'rows', 'num_rows', 'num_cols', 'insert_after_index'.
    """
    num_rows = table_data['num_rows']
    num_cols = table_data['num_cols']
    rows_data = table_data['rows']
    insert_index = table_data['insert_after_index']

    # Build the merge grid upfront (needed for text population and formatting)
    _grid, merges = _build_merge_grid(rows_data, num_rows, num_cols)

    # --- Insert table + merge in one batch ---
    init_requests = [{
        'insertTable': {
            'location': {'index': insert_index, 'tabId': tab_id},
            'rows': num_rows,
            'columns': num_cols,
        }
    }]
    # mergeTableCells only needs row/col indices and the table start location
    # (insert_index + 1), so no doc re-read is required between insert and merge.
    for m in merges:
        init_requests.append({
            'mergeTableCells': {
                'tableRange': {
                    'tableCellLocation': {
                        'tableStartLocation': {'index': insert_index + 1, 'tabId': tab_id},
                        'rowIndex': m['row'],
                        'columnIndex': m['col'],
                    },
                    'rowSpan': m['rowspan'],
                    'columnSpan': m['colspan'],
                }
            }
        })
    svc.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': init_requests},
    ).execute()

    # --- Populate cells with text (backwards to preserve indices) ---
    _, table_element = _find_table_in_tab(svc, doc_id, tab_id, insert_index)
    if not table_element:
        return

    cell_requests = []
    # Track which (row_idx, cell_idx) we've already written to avoid
    # writing into spanned-over cells that were merged away.
    written = set()

    for row_idx in range(num_rows - 1, -1, -1):
        table_row = table_element.get('tableRows', [])[row_idx]
        doc_cells = table_row.get('tableCells', [])

        # Walk the grid for this row to map grid columns to doc cells.
        # After merging, each merged region occupies exactly one doc cell
        # in the row. We track doc_cell_idx accordingly.
        row_reqs = []
        doc_cell_idx = 0
        prev_entry = None
        for grid_col in range(num_cols):
            entry = _grid[row_idx][grid_col] if grid_col < len(_grid[row_idx]) else None
            if entry is None:
                doc_cell_idx += 1
                prev_entry = None
                continue
            # Colspan continuation — same cell as the previous grid_col
            if entry is prev_entry:
                continue
            prev_entry = entry

            src_row, src_cell, cell_data = entry
            # Spanned-over by a cell from another row (rowspan).
            # The merged cell still occupies a doc cell slot.
            if src_row != row_idx:
                doc_cell_idx += 1
                continue

            written.add((src_row, src_cell))
            cell_text = cell_data['text'].strip()

            if cell_text and doc_cell_idx < len(doc_cells):
                cell = doc_cells[doc_cell_idx]
                cell_start = cell['content'][0]['paragraph']['elements'][0]['startIndex']

                row_reqs.append({
                    'insertText': {
                        'location': {'index': cell_start, 'tabId': tab_id},
                        'text': cell_text,
                    }
                })

            doc_cell_idx += 1

        # Reverse within-row order so right-most cells (highest indices)
        # are inserted first, preventing index shifts from invalidating
        # later requests in the same row.
        cell_requests.extend(reversed(row_reqs))

    if cell_requests:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': cell_requests},
        ).execute()

    # --- Reset inherited styles on all cells ---
    # Tables inserted at positions with heading/italic/etc. formatting inherit
    # those styles. Reset every cell to plain NORMAL_TEXT before applying
    # specific formatting.
    _, table_element = _find_table_in_tab(svc, doc_id, tab_id, insert_index)
    if not table_element:
        return

    reset_requests = []
    for row_idx in range(num_rows):
        table_row = table_element.get('tableRows', [])[row_idx]
        doc_cells = table_row.get('tableCells', [])
        for doc_cell in doc_cells:
            cell_start = doc_cell['content'][0]['paragraph']['elements'][0]['startIndex']
            cell_end = doc_cell['content'][-1].get('endIndex', cell_start)
            if cell_end > cell_start:
                reset_requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': cell_start,
                            'endIndex': cell_end,
                            'tabId': tab_id,
                        },
                        'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT'},
                        'fields': 'namedStyleType',
                    }
                })
                reset_requests.append({
                    'updateTextStyle': {
                        'range': {
                            'startIndex': cell_start,
                            'endIndex': cell_end,
                            'tabId': tab_id,
                        },
                        'textStyle': {
                            'bold': False,
                            'italic': False,
                            'fontSize': {'magnitude': 11, 'unit': 'PT'},
                            'foregroundColor': {'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}},
                        },
                        'fields': 'bold,italic,fontSize,foregroundColor',
                    }
                })
    if reset_requests:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': reset_requests},
        ).execute()

    # --- Apply formatting: bold + background for header cells, inline formatting for data cells ---
    has_formatting = any(
        c.get('is_header') or c.get('is_subheader') or c.get('formats')
        for row in rows_data for c in row
    )
    if not has_formatting:
        return

    # Re-read after reset to get current indices
    _, table_element = _find_table_in_tab(svc, doc_id, tab_id, insert_index)
    if not table_element:
        return

    fmt_requests = []
    for row_idx in range(num_rows):
        if row_idx >= len(rows_data):
            continue
        row_data = rows_data[row_idx]
        table_row = table_element.get('tableRows', [])[row_idx]
        doc_cells = table_row.get('tableCells', [])

        # Check if any cell in this row is a header or subheader
        row_has_header = any(c.get('is_header') for c in row_data)
        row_has_subheader = any(c.get('is_subheader') for c in row_data)

        doc_cell_idx = 0
        grid_col = 0
        for cell_data in row_data:
            cs = cell_data.get('colspan', 1)
            # Skip grid columns occupied by earlier rowspans
            while grid_col < num_cols and _grid[row_idx][grid_col] is not None:
                src_row, _, _ = _grid[row_idx][grid_col]
                if src_row == row_idx:
                    break
                grid_col += 1
                doc_cell_idx += 1

            if doc_cell_idx >= len(doc_cells):
                break

            cell = doc_cells[doc_cell_idx]
            cell_start = cell['content'][0]['paragraph']['elements'][0]['startIndex']
            # End of cell content
            cell_end = cell['content'][-1].get('endIndex', cell_start)

            cell_text = cell_data['text'].strip()

            if cell_data.get('is_header') or row_has_header:
                # Bold the text
                if cell_text:
                    fmt_requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': cell_start,
                                'endIndex': cell_start + len(cell_text),
                                'tabId': tab_id,
                            },
                            'textStyle': {'bold': True},
                            'fields': 'bold',
                        }
                    })

                # Background colour on the cell
                fmt_requests.append({
                    'updateTableCellStyle': {
                        'tableCellStyle': {
                            'backgroundColor': {
                                'color': {'rgbColor': _BG_TABLE_HEADER},
                            },
                        },
                        'tableRange': {
                            'tableCellLocation': {
                                'tableStartLocation': {'index': insert_index + 1, 'tabId': tab_id},
                                'rowIndex': row_idx,
                                'columnIndex': grid_col,
                            },
                            'rowSpan': 1,
                            'columnSpan': 1,
                        },
                        'fields': 'backgroundColor',
                    }
                })
            elif cell_data.get('is_subheader') or row_has_subheader:
                # Bold the text
                if cell_text:
                    fmt_requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': cell_start,
                                'endIndex': cell_start + len(cell_text),
                                'tabId': tab_id,
                            },
                            'textStyle': {'bold': True},
                            'fields': 'bold',
                        }
                    })

                # Subheader background colour
                fmt_requests.append({
                    'updateTableCellStyle': {
                        'tableCellStyle': {
                            'backgroundColor': {
                                'color': {'rgbColor': _BG_TABLE_SUBHEADER},
                            },
                        },
                        'tableRange': {
                            'tableCellLocation': {
                                'tableStartLocation': {'index': insert_index + 1, 'tabId': tab_id},
                                'rowIndex': row_idx,
                                'columnIndex': grid_col,
                            },
                            'rowSpan': 1,
                            'columnSpan': 1,
                        },
                        'fields': 'backgroundColor',
                    }
                })
            elif cell_text and cell_data.get('formats'):
                # Apply inline bold/italic/link formatting for data cells
                leading = len(cell_data['text']) - len(cell_data['text'].lstrip())
                bold_starts = []
                italic_starts = []
                link_starts = []
                for fmt_entry in cell_data['formats']:
                    fmt_type = fmt_entry[0]
                    pos = fmt_entry[1]
                    pos_data = fmt_entry[2] if len(fmt_entry) > 2 else None
                    adj_pos = pos - leading
                    if adj_pos < 0:
                        adj_pos = 0
                    if adj_pos > len(cell_text):
                        adj_pos = len(cell_text)
                    if fmt_type == 'bold_start':
                        bold_starts.append(adj_pos)
                    elif fmt_type == 'bold_end' and bold_starts:
                        start = bold_starts.pop()
                        if start < adj_pos:
                            fmt_requests.append({
                                'updateTextStyle': {
                                    'range': {
                                        'startIndex': cell_start + start,
                                        'endIndex': cell_start + adj_pos,
                                        'tabId': tab_id,
                                    },
                                    'textStyle': {'bold': True},
                                    'fields': 'bold',
                                }
                            })
                    elif fmt_type == 'italic_start':
                        italic_starts.append(adj_pos)
                    elif fmt_type == 'italic_end' and italic_starts:
                        start = italic_starts.pop()
                        if start < adj_pos:
                            fmt_requests.append({
                                'updateTextStyle': {
                                    'range': {
                                        'startIndex': cell_start + start,
                                        'endIndex': cell_start + adj_pos,
                                        'tabId': tab_id,
                                    },
                                    'textStyle': {'italic': True},
                                    'fields': 'italic',
                                }
                            })
                    elif fmt_type == 'link_start':
                        link_starts.append((adj_pos, pos_data))
                    elif fmt_type == 'link_end' and link_starts:
                        start, href = link_starts.pop()
                        if start < adj_pos and href:
                            fmt_requests.append({
                                'updateTextStyle': {
                                    'range': {
                                        'startIndex': cell_start + start,
                                        'endIndex': cell_start + adj_pos,
                                        'tabId': tab_id,
                                    },
                                    'textStyle': {'link': {'url': href}},
                                    'fields': 'link',
                                }
                            })

            grid_col += cs
            doc_cell_idx += 1

    if fmt_requests:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': fmt_requests},
        ).execute()


# ---------------------------------------------------------------------------
# Reverse conversion: Google Doc → MadCap Flare HTML
# ---------------------------------------------------------------------------

def _colour_match(actual, expected, tol=0.05):
    """Return True if actual RGB dict matches expected within tolerance."""
    if not actual or not expected:
        return False
    for k in ('red', 'green', 'blue'):
        if abs(actual.get(k, 0) - expected.get(k, 0)) > tol:
            return False
    return True


def _detect_para_region(para_style):
    """Detect special region type from paragraph shading colour.

    Returns one of 'overview', 'note', 'warning', 'snippet' or None.
    """
    shading = (para_style or {}).get('shading', {})
    bg = shading.get('backgroundColor', {}).get('color', {}).get('rgbColor')
    if not bg:
        return None
    if _colour_match(bg, _BG_OVERVIEW):
        return 'overview'
    if _colour_match(bg, _BG_NOTE):
        return 'note'
    if _colour_match(bg, _BG_WARNING):
        return 'warning'
    if _colour_match(bg, _BG_SNIPPET):
        return 'snippet'
    return None


def _detect_text_region(text_style):
    """Detect inline highlight type from text background colour.

    Returns 'variable', 'image', or None.
    """
    bg = (text_style or {}).get('backgroundColor', {}).get('color', {}).get('rgbColor')
    if not bg:
        return None
    if _colour_match(bg, _BG_VARIABLE):
        return 'variable'
    if _colour_match(bg, _BG_IMAGE):
        return 'image'
    return None


def _build_reverse_url_map(kb_root):
    """Invert the filename→URL map to URL→filename.htm."""
    forward = _load_url_map(kb_root)
    reverse = {}
    for filename_lower, url in forward.items():
        reverse[url] = f"{filename_lower}.htm"
    return reverse


def _build_reverse_variable_map(variables):
    """Invert variables dict (name→value) to value→name.

    When multiple variables share the same value the first one wins.
    """
    reverse = {}
    for name, value in variables.items():
        if value and value not in reverse:
            reverse[value] = name
    return reverse


def _reverse_resolve_href(href, reverse_url_map):
    """Convert a Zendesk URL back to a local .htm href, or leave as-is."""
    if not href:
        return href
    # Already a local file reference
    if not href.startswith(('http://', 'https://')):
        return href
    # Strip fragment before lookup, re-attach after
    fragment = ''
    if '#' in href:
        href_clean, fragment = href.rsplit('#', 1)
        fragment = '#' + fragment
    else:
        href_clean = href
    local = reverse_url_map.get(href_clean)
    if local:
        return local + fragment
    return href


def _find_htm_file(article_name, topics_dir):
    """Find the .htm file whose H1 matches article_name (case-insensitive).

    Returns the absolute path, or None if not found.
    """
    import re
    import glob

    # Try direct filename match first
    candidate = os.path.join(topics_dir, f"{article_name}.htm")
    if os.path.isfile(candidate):
        return candidate

    # Search by H1 content
    for htm_path in glob.glob(os.path.join(topics_dir, '*.htm')):
        try:
            with open(htm_path, 'r', encoding='utf-8') as f:
                content = f.read(4096)  # H1 is always near the top
            m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL | re.IGNORECASE)
            if m:
                h1_text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if h1_text.lower() == article_name.lower():
                    return htm_path
        except (OSError, UnicodeDecodeError):
            continue
    return None


def _extract_snippet_refs(htm_path):
    """Extract ordered list of snippet src paths from an .htm file.

    Returns list of src attribute values (e.g. '../Snippets/Foo.flsnp').
    """
    import re

    with open(htm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    refs = re.findall(
        r'<MadCap:snippet(?:Block|Text)\s+src="([^"]+)"\s*/\s*>',
        content, re.IGNORECASE)
    return refs


def _extract_col_styles(htm_path):
    """Extract <col> style attributes from the original .htm file.

    Returns a list of lists, one per table in document order.
    Each inner list contains the style attribute strings (or '') for each <col>.
    """
    import re

    with open(htm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tables = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL | re.IGNORECASE)
    result = []
    for table_html in tables:
        cols = re.findall(r'<col\s+style="([^"]*)"[^/]*/>', table_html, re.IGNORECASE)
        if not cols:
            cols = re.findall(r'<col\s+style="([^"]*)"[^>]*>', table_html, re.IGNORECASE)
        result.append(cols)
    return result


def _extract_heading_anchors(htm_path):
    """Extract named anchors from headings in the original .htm file.

    Returns a dict mapping heading text (lowercase, stripped) to anchor name.
    """
    import re

    with open(htm_path, 'r', encoding='utf-8') as f:
        content = f.read()

    anchors = {}
    for m in re.finditer(
        r'<h[1-6][^>]*>\s*<a\s+name="([^"]+)"[^>]*>\s*</a>\s*(.*?)\s*</h[1-6]>',
        content, re.DOTALL | re.IGNORECASE
    ):
        anchor_name = m.group(1)
        heading_text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if heading_text:
            anchors[heading_text.lower()] = anchor_name
    return anchors


def _read_doc_tabs(doc_id):
    """Read all [edit] and [new] tabs from a Google Doc.

    Returns a list of dicts:
        {'title': str, 'type': 'edit'|'new', 'article_name': str,
         'body_content': list, 'url_line': str or None}
    """
    svc = get_docs_service()
    doc = svc.documents().get(
        documentId=doc_id, includeTabsContent=True
    ).execute()

    tabs = []
    for tab in doc.get('tabs', []):
        title = tab.get('tabProperties', {}).get('title', '')
        if title.startswith('[edit] '):
            tab_type = 'edit'
            article_name = title[len('[edit] '):]
        elif title.startswith('[new] '):
            tab_type = 'new'
            article_name = title[len('[new] '):]
        else:
            continue

        body = tab.get('documentTab', {}).get('body', {})
        body_content = body.get('content', [])

        # The first line in [edit] tabs may be a Zendesk URL — detect and separate it
        url_line = None
        if tab_type == 'edit' and body_content:
            first_para = body_content[0] if body_content else None
            if first_para and 'paragraph' in first_para:
                elements = first_para['paragraph'].get('elements', [])
                if elements:
                    text_run = elements[0].get('textRun', {})
                    content_text = text_run.get('content', '').strip()
                    link = text_run.get('textStyle', {}).get('link', {}).get('url', '')
                    if link and content_text.startswith('http'):
                        url_line = content_text
                        body_content = body_content[1:]  # skip URL paragraph

        tabs.append({
            'title': title,
            'type': tab_type,
            'article_name': article_name,
            'body_content': body_content,
            'url_line': url_line,
        })

    return tabs


def _runs_to_html(elements, reverse_url_map, reverse_var_map, variables):
    """Convert a list of Google Docs paragraph elements (text runs) to HTML.

    Handles bold, italic, links, variables (purple highlight),
    and image placeholders (yellow highlight).

    Returns the inner HTML string (no wrapping <p> tag).
    """
    import re

    parts = []
    for el in elements:
        text_run = el.get('textRun')
        if not text_run:
            continue
        content = text_run.get('content', '')
        if content == '\n':
            continue  # paragraph-ending newline
        style = text_run.get('textStyle', {})

        # Detect inline highlights
        inline_type = _detect_text_region(style)

        if inline_type == 'image':
            # Convert [Image: path] back to <img>
            m = re.match(r'\[Image:\s*(.+?)\]', content)
            if m:
                img_path = m.group(1)
                parts.append(f'<img src="{img_path}" />')
                continue

        if inline_type == 'variable':
            # Try to find the variable name for this value
            text_val = content.rstrip('\n').rstrip()
            var_name = reverse_var_map.get(text_val)
            if var_name:
                parts.append(f'<MadCap:variable name="{var_name}" />')
                continue

        # Normal text run — apply formatting
        text = content.rstrip('\n')
        if not text:
            continue

        # Replace vertical tab with <br />
        text = text.replace('\v', '<br />')

        # Handle link
        link_url = style.get('link', {}).get('url', '')
        if link_url:
            link_url = _reverse_resolve_href(link_url, reverse_url_map)

        is_bold = style.get('bold', False)
        is_italic = style.get('italic', False)

        fragment = text
        if is_bold:
            fragment = f'<b>{fragment}</b>'
        if is_italic:
            fragment = f'<i>{fragment}</i>'
        if link_url:
            fragment = f'<a href="{link_url}">{fragment}</a>'

        parts.append(fragment)

    return ''.join(parts)


def _table_to_html(table_element, reverse_url_map, reverse_var_map, variables, col_styles=None):
    """Convert a Google Docs table element to MadCap Flare HTML.

    Args:
        table_element: The 'table' dict from Google Docs API.
        reverse_url_map: URL→filename mapping.
        reverse_var_map: value→variable name mapping.
        variables: original variables dict.
        col_styles: optional list of style strings for <col> elements.

    Returns an HTML string for the <table>.
    """
    rows = table_element.get('tableRows', [])
    if not rows:
        return ''

    lines = ['<table>']

    # Add <col> styles if available
    if col_styles:
        for style in col_styles:
            if style:
                lines.append(f'    <col style="{style}"/>')
            else:
                lines.append('    <col />')

    for row_idx, row in enumerate(rows):
        cells = row.get('tableCells', [])
        is_header_row = row_idx == 0

        if is_header_row:
            lines.append('    <thead>')
        elif row_idx == 1:
            lines.append('    <tbody>')

        lines.append('        <tr>')
        for cell in cells:
            cell_tag = 'th' if is_header_row else 'td'

            # Check for colspan/rowspan from cell style
            cell_style = cell.get('tableCellStyle', {})
            # Google Docs doesn't store colspan/rowspan the same way — cells
            # that are merged are simply absent from the row.  We emit plain
            # cells here; MadCap Flare files rarely use colspan/rowspan.

            # Extract text from cell paragraphs
            cell_parts = []
            cell_content = cell.get('content', [])
            for para in cell_content:
                if 'paragraph' not in para:
                    continue
                elements = para['paragraph'].get('elements', [])
                inner = _runs_to_html(
                    elements, reverse_url_map, reverse_var_map, variables)
                if inner.strip():
                    if cell_tag == 'th':
                        # Strip bold wrapping from header cells (th is inherently bold)
                        import re as _re
                        inner = _re.sub(r'^<b>(.*)</b>$', r'\1', inner)
                    cell_parts.append(inner)

            cell_html = '</p><p>'.join(cell_parts)
            if cell_parts:
                cell_html = f'<p>{cell_html}</p>'

            lines.append(f'            <{cell_tag}>{cell_html}</{cell_tag}>')

        lines.append('        </tr>')

        if is_header_row:
            lines.append('    </thead>')

    # Close tbody if we had data rows
    if len(rows) > 1:
        lines.append('    </tbody>')
    lines.append('</table>')

    return '\n'.join(lines)


def _doc_to_htm_content(body_content, kb_path, variables, reverse_url_map,
                        reverse_var_map, original_htm_path=None, kb_type='omni'):
    """Convert Google Docs body content back to MadCap Flare HTML.

    Args:
        body_content: List of structural elements from Google Docs API.
        kb_path: Root path of the knowledge base repo.
        variables: Dict of variable name → value.
        reverse_url_map: Dict of Zendesk URL → local filename.
        reverse_var_map: Dict of variable value → variable name.
        original_htm_path: Path to the original .htm file (for [edit] tabs).
        kb_type: 'core' or 'omni' — determines HTML wrapper format.

    Returns:
        (html_string, snippet_updates) where snippet_updates is a list of
        (abs_path_to_flsnp, new_body_html) tuples for modified snippets.
    """
    import re
    global _snippet_bodies_collected
    _snippet_bodies_collected = []

    topics_dir = os.path.join(kb_path, 'Content', 'Resources', 'Topics')

    # Load original snippet refs and heading anchors if we have an original file
    snippet_refs = _extract_snippet_refs(original_htm_path) if original_htm_path else []
    heading_anchors = _extract_heading_anchors(original_htm_path) if original_htm_path else {}
    col_styles_by_table = _extract_col_styles(original_htm_path) if original_htm_path else []

    # Identify snippet regions by scanning for consecutive green-shaded paragraphs
    snippet_idx = 0

    # First pass: identify structure (regions, headings, lists, tables, paragraphs)
    body_html_parts = []
    current_region = None  # ('overview'|'note'|'warning'|'snippet', start_idx)
    region_parts = []
    list_stack = []  # stack of ('ul'|'ol', indent_level)
    table_counter = 0

    i = 0
    while i < len(body_content):
        element = body_content[i]

        # Handle tables
        if 'table' in element:
            # Close any open list
            while list_stack:
                tag, _ = list_stack.pop()
                body_html_parts.append(f'</{tag}>')

            col_styles = None
            if table_counter < len(col_styles_by_table):
                col_styles = col_styles_by_table[table_counter]
            table_counter += 1

            table_html = _table_to_html(
                element['table'], reverse_url_map, reverse_var_map,
                variables, col_styles)

            if current_region:
                region_parts.append(table_html)
            else:
                body_html_parts.append(table_html)
            i += 1
            continue

        # Handle paragraphs
        if 'paragraph' not in element:
            i += 1
            continue

        para = element['paragraph']
        para_style = para.get('paragraphStyle', {})
        elements = para.get('elements', [])
        named_style = para_style.get('namedStyleType', 'NORMAL_TEXT')

        # Detect paragraph-level region
        region_type = _detect_para_region(para_style)

        # Detect bullet/list
        bullet = para.get('bullet')
        nesting_level = bullet.get('nestingLevel', 0) if bullet else None
        list_id = bullet.get('listId', '') if bullet else None

        # Get the list glyph type to distinguish ul vs ol
        is_ordered = False
        if bullet:
            # Check the document's list properties for this list
            # Google Docs uses 'listId' and 'nestingLevel'
            # We infer ordered vs unordered from the glyph format
            glyph_type = bullet.get('textStyle', {})
            # Simpler heuristic: check namedStyleType or list properties
            # In practice, ordered lists use NUMBERED_* presets
            # We can check if the list uses number glyphs by looking at
            # paragraph namedStyleType — but the safest approach is checking
            # the list's glyph format from the document's lists dict.
            # Since we don't have the full document here, we use a content
            # heuristic: if the first text run starts with a digit pattern, it's ordered.
            pass  # default to unordered; see below for override

        # Handle region transitions
        if region_type and region_type != (current_region[0] if current_region else None):
            # Close previous region
            if current_region:
                # Close any open list inside the region
                while list_stack:
                    tag, _ = list_stack.pop()
                    region_parts.append(f'</{tag}>')
                _flush_region(current_region[0], region_parts, body_html_parts,
                              snippet_refs, snippet_idx, topics_dir, variables)
                if current_region[0] == 'snippet':
                    snippet_idx += 1
                region_parts = []
            current_region = (region_type, i)
        elif not region_type and current_region:
            # Exiting a region
            while list_stack:
                tag, _ = list_stack.pop()
                region_parts.append(f'</{tag}>')
            _flush_region(current_region[0], region_parts, body_html_parts,
                          snippet_refs, snippet_idx, topics_dir, variables)
            if current_region[0] == 'snippet':
                snippet_idx += 1
            region_parts = []
            current_region = None

        # Convert the paragraph content
        inner_html = _runs_to_html(
            elements, reverse_url_map, reverse_var_map, variables)

        target = region_parts if current_region else body_html_parts

        # Determine output tag
        if named_style.startswith('HEADING_'):
            level = int(named_style.split('_')[1])
            heading_text_plain = re.sub(r'<[^>]+>', '', inner_html).strip()
            anchor = heading_anchors.get(heading_text_plain.lower(), '')
            if level == 1:
                target.append(f'<h1 class="hide">{inner_html}</h1>')
            elif anchor:
                target.append(
                    f'<h{level}><a name="{anchor}"></a>{inner_html}</h{level}>')
            else:
                target.append(f'<h{level}>{inner_html}</h{level}>')
        elif bullet is not None:
            # List item
            depth = nesting_level if nesting_level is not None else 0

            # Determine list type from glyph
            list_props = bullet
            glyph_format = list_props.get('textStyle', {})
            # Heuristic: check if the list was ordered in the original
            # For simplicity, we use NUMBERED detection from list properties
            # Default to 'ul'; the glyph symbol gives us a better clue
            glyph_symbol = list_props.get('glyphSymbol', '')
            if not glyph_symbol:
                # No glyph symbol usually means ordered list
                is_ordered = True
            else:
                is_ordered = False

            list_tag = 'ol' if is_ordered else 'ul'

            # Manage list nesting
            current_depth = len(list_stack) - 1

            if depth > current_depth:
                # Open new list level(s)
                while len(list_stack) - 1 < depth:
                    open_tag = list_tag
                    if open_tag == 'ol':
                        target.append('<ol start="1">')
                    else:
                        target.append(f'<{open_tag}>')
                    list_stack.append((open_tag, len(list_stack)))
            elif depth < current_depth:
                # Close list level(s)
                while len(list_stack) - 1 > depth:
                    close_tag, _ = list_stack.pop()
                    target.append(f'</li>')
                    target.append(f'</{close_tag}>')

            target.append(f'<li><p>{inner_html}</p></li>')
        else:
            # Close any open list
            while list_stack:
                tag, _ = list_stack.pop()
                target.append(f'</{tag}>')

            # Regular paragraph
            if inner_html.strip():
                target.append(f'<p>{inner_html}</p>')

        i += 1

    # Close any remaining open region
    if current_region:
        while list_stack:
            tag, _ = list_stack.pop()
            region_parts.append(f'</{tag}>')
        _flush_region(current_region[0], region_parts, body_html_parts,
                      snippet_refs, snippet_idx, topics_dir, variables)
        region_parts = []
    else:
        while list_stack:
            tag, _ = list_stack.pop()
            body_html_parts.append(f'</{tag}>')

    # Build the complete HTML document
    body_inner = '\n'.join(f'        {line}' for line in body_html_parts if line)

    if kb_type == 'core':
        html = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<html xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd">\n'
            '    <head>\n'
            '    </head>\n'
            '    <body>\n'
            f'{body_inner}\n'
            '    </body>\n'
            '</html>'
        )
    else:
        html = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<html xmlns:MadCap="http://www.madcapsoftware.com/Schemas/MadCap.xsd"'
            ' xml:lang="en-us" MadCap:onlyLocalStylesheets="True">\n'
            '    <head>\n'
            '        <title></title>\n'
            '        <link href="../Stylesheets/Styles.css"'
            ' rel="stylesheet" type="text/css" />\n'
            '    </head>\n'
            '    <body>\n'
            f'{body_inner}\n'
            '    </body>\n'
            '</html>'
        )

    # Determine which snippets were modified
    snippet_updates = []
    if original_htm_path and snippet_refs:
        for idx, src in enumerate(snippet_refs):
            abs_snippet = os.path.normpath(os.path.join(topics_dir, src))
            if not os.path.isfile(abs_snippet):
                continue
            # Read current snippet body
            with open(abs_snippet, 'r', encoding='utf-8') as f:
                raw = f.read()
            body_match = re.search(r'<body[^>]*>(.*?)</body>', raw, re.DOTALL)
            current_body = body_match.group(1).strip() if body_match else raw.strip()

            # Get the converted snippet body from our green region
            if idx < len(_snippet_bodies_collected):
                new_body = _snippet_bodies_collected[idx]
                # Normalize whitespace for comparison
                import textwrap
                current_norm = ' '.join(current_body.split())
                new_norm = ' '.join(new_body.split())
                if current_norm != new_norm:
                    snippet_updates.append((abs_snippet, new_body))

    return html, snippet_updates


# Collects snippet region HTML bodies during conversion (module-level for simplicity)
_snippet_bodies_collected = []


def _flush_region(region_type, parts, output_parts, snippet_refs, snippet_idx,
                  topics_dir, variables):
    """Flush a completed special region into the output.

    For snippet regions: emit the original <MadCap:snippetBlock> reference and
    collect the body for later comparison.
    For overview/note/warning: wrap in the appropriate div.
    """
    global _snippet_bodies_collected

    content = '\n'.join(f'    {p}' for p in parts if p)

    if region_type == 'snippet':
        # Collect the body for snippet comparison
        body_html = '\n'.join(parts)
        _snippet_bodies_collected.append(body_html)

        # Emit the original snippet reference if available
        if snippet_idx < len(snippet_refs):
            src = snippet_refs[snippet_idx]
            output_parts.append(f'<MadCap:snippetBlock src="{src}" />')
        else:
            # No matching snippet ref — emit inline content with warning
            output_parts.append('<!-- Warning: snippet region could not be mapped to a .flsnp reference -->')
            output_parts.extend(parts)
    elif region_type == 'overview':
        output_parts.append('<div class="overview">')
        output_parts.extend(f'    {p}' for p in parts if p)
        output_parts.append('</div>')
    elif region_type == 'note':
        if len(parts) == 1:
            # Single paragraph note
            p_content = parts[0]
            if p_content.startswith('<p>') and p_content.endswith('</p>'):
                inner = p_content[3:-4]
                output_parts.append(f'<p class="note">{inner}</p>')
            else:
                output_parts.append(f'<div class="note">')
                output_parts.extend(f'    {p}' for p in parts if p)
                output_parts.append('</div>')
        else:
            output_parts.append('<div class="note">')
            output_parts.extend(f'    {p}' for p in parts if p)
            output_parts.append('</div>')
    elif region_type == 'warning':
        output_parts.append('<div class="warning">')
        output_parts.extend(f'    {p}' for p in parts if p)
        output_parts.append('</div>')


def _derive_filename(h1_text):
    """Derive a .htm filename from H1 heading text.

    Preserves the original text as-is for the filename (spaces included),
    matching MadCap Flare's convention. Only strips characters invalid
    in filenames.
    """
    import re
    # Remove characters that are invalid in Windows filenames
    clean = re.sub(r'[<>:"/\\|?*]', '', h1_text).strip()
    if not clean:
        clean = 'Untitled'
    return f"{clean}.htm"


def apply_drafts(doc_id, kb_path):
    """Read Google Doc tabs and apply changes back to .htm files.

    Args:
        doc_id:  Google Docs document ID.
        kb_path: Absolute path to the knowledge base repo root.

    Returns a dict summary: {'modified': [...], 'created': [...], 'snippets_updated': [...]}
    """
    import json
    import re

    topics_dir = os.path.join(kb_path, 'Content', 'Resources', 'Topics')
    if not os.path.isdir(topics_dir):
        print(f"Error: Topics directory not found: {topics_dir}")
        return {'modified': [], 'created': [], 'snippets_updated': [], 'errors': [f'Topics dir not found: {topics_dir}']}

    # Determine KB type
    kb_basename = os.path.basename(kb_path.rstrip(os.sep))
    kb_type = 'core' if 'core' in kb_basename.lower() else 'omni'
    print(f"Knowledge base: {kb_basename} (type: {kb_type})")

    # Load variables, URL maps, and build reverse maps
    variables = _load_variables(kb_path)
    reverse_url_map = _build_reverse_url_map(kb_path)
    reverse_var_map = _build_reverse_variable_map(variables)

    print(f"  Variables: {len(variables)}, URL mappings: {len(reverse_url_map)}")

    # Read tabs from Google Doc
    tabs = _read_doc_tabs(doc_id)
    print(f"  Found {len(tabs)} article tab(s)")

    summary = {'modified': [], 'created': [], 'snippets_updated': [], 'errors': []}

    for tab in tabs:
        article_name = tab['article_name']
        tab_type = tab['type']
        body_content = tab['body_content']

        print(f"\n  Processing: [{tab_type}] {article_name}")

        original_htm_path = None
        if tab_type == 'edit':
            original_htm_path = _find_htm_file(article_name, topics_dir)
            if not original_htm_path:
                msg = f"Could not find .htm file for '{article_name}'"
                print(f"    Error: {msg}")
                summary['errors'].append(msg)
                continue

        # Convert Google Doc content to HTML
        html, snippet_updates = _doc_to_htm_content(
            body_content, kb_path, variables, reverse_url_map,
            reverse_var_map, original_htm_path, kb_type)

        if tab_type == 'edit':
            # Overwrite the original file
            with open(original_htm_path, 'w', encoding='utf-8') as f:
                f.write(html)
            rel_path = os.path.relpath(original_htm_path, kb_path)
            summary['modified'].append(rel_path)
            print(f"    Updated: {rel_path}")
        else:
            # New article — derive filename from H1
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
            if h1_match:
                h1_text = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            else:
                h1_text = article_name
            filename = _derive_filename(h1_text)
            new_path = os.path.join(topics_dir, filename)

            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(html)
            rel_path = os.path.relpath(new_path, kb_path)
            summary['created'].append(rel_path)
            print(f"    Created: {rel_path}")

        # Write updated snippets
        for snippet_path, new_body in snippet_updates:
            with open(snippet_path, 'r', encoding='utf-8') as f:
                raw = f.read()
            # Replace body content
            updated = re.sub(
                r'(<body[^>]*>).*?(</body>)',
                rf'\1\n{new_body}\n\2',
                raw, flags=re.DOTALL)
            with open(snippet_path, 'w', encoding='utf-8') as f:
                f.write(updated)
            rel_path = os.path.relpath(snippet_path, kb_path)
            summary['snippets_updated'].append(rel_path)
            print(f"    Snippet updated: {rel_path}")

    # Print JSON summary
    print(f"\n{json.dumps(summary, indent=2)}")
    return summary


def create_article_tabs(doc_id, rows, kb_path):
    """Create tabs in the doc for each primary-update article.

    For 'Update' articles: finds the matching .htm file in kb_path, converts
    HTML to Google Docs format (resolving snippets, variables, and applying
    background colours to overview/note/warning/snippet/variable content),
    and writes it to a new tab named '[edit] Article'.
    For 'Create' articles: creates a blank tab named '[new] Article'.

    All content is prepared upfront, then tabs are created and populated in
    minimal API calls.

    Args:
        doc_id:  Google Docs file ID.
        rows:    Parsed scope table rows (from write_doc_scope).
        kb_path: Path to the knowledge base repo root (e.g. 'Cin7 Omni knowledge base/').
    """
    import glob
    import re

    svc = get_docs_service()
    articles = _get_scope_articles(rows)

    if not articles:
        print("No articles found to create tabs for.")
        return

    # Determine the Topics and Snippets directories
    topics_dir = os.path.join(kb_path, 'Content', 'Resources', 'Topics')
    if not os.path.isdir(topics_dir):
        print(f"Topics directory not found: {topics_dir}")
        return

    # Load variables from .flvar files
    variables = _load_variables(kb_path)

    # Load filename→Zendesk URL mapping
    url_map = _load_url_map(kb_path)

    # --- Phase 1: Prepare all content upfront ---
    tab_specs = []  # List of {title, action, content} dicts
    for article in articles:
        action = article['action'].lower()
        name = article['name']

        if action == 'update':
            prefix = '[edit]'
        elif action == 'create':
            prefix = '[new]'
        else:
            continue

        tab_title = _truncate_tab_name(prefix, name)
        spec = {'title': tab_title, 'action': action, 'name': name, 'content': None}

        if action == 'update' and kb_path:
            htm_file = None
            candidate = os.path.join(topics_dir, f"{name}.htm")
            if os.path.isfile(candidate):
                htm_file = candidate
            else:
                matches = glob.glob(os.path.join(topics_dir, '**', f"{name}.htm"), recursive=True)
                if matches:
                    htm_file = matches[0]

            if htm_file:
                with open(htm_file, 'r', encoding='utf-8') as f:
                    raw_html = f.read()
                # Extract the body content
                body_match = re.search(r'<body[^>]*>(.*)</body>', raw_html, re.DOTALL)
                htm_body = body_match.group(1) if body_match else raw_html

                # Build a URL prefix line if the article has a Zendesk URL
                article_url = url_map.get(name.lower(), '')
                url_prefix = f"{article_url}\n" if article_url else ''
                prefix_len = len(url_prefix)

                text_requests, format_requests = _htm_to_doc_requests(
                    htm_body, topics_dir, variables,
                    start_index=1 + prefix_len, url_map=url_map)

                # Prepend the URL text and add a link format request
                if url_prefix:
                    text_requests.insert(0, {
                        'insertText': {
                            'location': {'index': 1},
                            'text': url_prefix,
                        }
                    })
                    format_requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': 1, 'endIndex': 1 + len(article_url)},
                            'textStyle': {'link': {'url': article_url}},
                            'fields': 'link',
                        }
                    })

                table_requests = [r for r in format_requests if r.get('_table')]
                fmt_requests = [r for r in format_requests if not r.get('_table')]
                spec['content'] = {
                    'text_requests': text_requests,
                    'fmt_requests': fmt_requests,
                    'table_requests': table_requests,
                    'source': os.path.basename(htm_file),
                }

        tab_specs.append(spec)

    if not tab_specs:
        print("No tabs to create.")
        return

    print(f"  Prepared content for {len(tab_specs)} tab(s)")

    # --- Phase 2: Delete existing tabs in one batch ---
    doc = svc.documents().get(documentId=doc_id, includeTabsContent=True).execute()
    existing_tabs = {
        tab['tabProperties']['title']: tab['tabProperties']['tabId']
        for tab in doc.get('tabs', [])
    }
    delete_requests = []
    for spec in tab_specs:
        if spec['title'] in existing_tabs:
            delete_requests.append({'deleteTab': {'tabId': existing_tabs[spec['title']]}})

    if delete_requests:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': delete_requests},
        ).execute()
        print(f"  Deleted {len(delete_requests)} existing tab(s)")

    # --- Phase 3: Create all tabs in one batch ---
    add_requests = [
        {'addDocumentTab': {'tabProperties': {'title': spec['title']}}}
        for spec in tab_specs
    ]
    result = svc.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': add_requests},
    ).execute()

    # Map each spec to its new tab ID from the batch response
    replies = result.get('replies', [])
    for i, spec in enumerate(tab_specs):
        if i < len(replies) and 'addDocumentTab' in replies[i]:
            spec['tab_id'] = replies[i]['addDocumentTab'].get('tabProperties', {}).get('tabId')
        else:
            spec['tab_id'] = None

    print(f"  Created {len(tab_specs)} tab(s)")

    # --- Phase 4: Populate each tab with its prepared content ---
    for spec in tab_specs:
        tab_id = spec.get('tab_id')
        if not tab_id:
            print(f"  Warning: no tab ID for '{spec['title']}'")
            continue

        content = spec.get('content')
        if not content:
            print(f"  '{spec['title']}' (blank)")
            continue

        # Insert text
        if content['text_requests']:
            for req in content['text_requests']:
                if 'insertText' in req:
                    req['insertText']['location']['tabId'] = tab_id
            svc.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': content['text_requests']},
            ).execute()

        # Apply formatting (headings, bold, italic, links, bullets)
        if content['fmt_requests']:
            for req in content['fmt_requests']:
                for key in ('updateParagraphStyle', 'createParagraphBullets',
                            'updateTextStyle'):
                    if key in req and 'range' in req[key]:
                        req[key]['range']['tabId'] = tab_id
                        break
            svc.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': content['fmt_requests']},
            ).execute()

        # Insert tables in reverse order (last table first) so that
        # each insertion only shifts indices below itself, keeping earlier
        # tables' insertion indices valid.
        for tbl in reversed(content['table_requests']):
            _insert_table_in_tab(svc, doc_id, tab_id, tbl)

        print(f"  '{spec['title']}' ← {content['source']}")


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
    f = service.files().create(body=metadata, media_body=media, fields='id, name').execute()
    print(f"Uploaded '{f['name']}' — id: {f['id']}")
    return f['id']


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

    ws = subparsers.add_parser('write-scope', help='Write scope content to a Google Doc')
    ws.add_argument('doc_id', help='Google Doc file ID')
    ws.add_argument('content', nargs='?', default=None, help='Content to write to the doc (use --content-file instead for reliability)')
    ws.add_argument('--content-file', help='Path to a file containing the scope content (avoids shell quoting issues)', default=None)
    ws.add_argument('--kb-path', help='Path to knowledge base repo root for article tabs', default=None)

    ad = subparsers.add_parser('apply-drafts', help='Apply Google Doc drafts back to .htm files')
    ad.add_argument('doc_id', help='Google Doc file ID')
    ad.add_argument('--kb-path', required=True, help='Absolute path to knowledge base repo root')

    args = parser.parse_args()

    if args.command == 'create-folder':
        create_folder(args.name, args.parent)
    elif args.command == 'create-doc':
        create_doc(args.name, args.parent)
    elif args.command == 'create-sheet':
        create_sheet(args.name, args.parent)
    elif args.command == 'upload':
        upload_file(args.path, args.parent, args.name)
    elif args.command == 'write-scope':
        content = args.content
        if args.content_file:
            with open(args.content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        if not content:
            print('Error: provide scope content either as a positional argument or via --content-file')
            raise SystemExit(1)
        rows = write_doc_scope(args.doc_id, content)
        if rows and args.kb_path:
            create_article_tabs(args.doc_id, rows, args.kb_path)
    elif args.command == 'apply-drafts':
        apply_drafts(args.doc_id, args.kb_path)
    else:
        parser.print_help()


# NOTE: Run all scripts with `python -B drive.py ...` to suppress __pycache__ creation.

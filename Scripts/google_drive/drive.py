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
    _GRAY,
    _RED,
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

    # Conditional formatting for "New" column (index 3)
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
                        'values': [{'userEnteredValue': '=$D2="No change"'}]
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

    args = parser.parse_args()

    if args.command == 'create-folder':
        create_folder(args.name, args.parent)
    elif args.command == 'create-doc':
        create_doc(args.name, args.parent)
    elif args.command == 'create-sheet':
        create_sheet(args.name, args.parent)
    elif args.command == 'upload':
        upload_file(args.path, args.parent, args.name)
    else:
        parser.print_help()


# NOTE: Run all scripts with `python -B drive.py ...` to suppress __pycache__ creation.

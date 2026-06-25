# #efefef
_GRAY   = {'red': 0.9373, 'green': 0.9373, 'blue': 0.9373}
# #c5d9f1
_BLUE   = {'red': 0.7725, 'green': 0.8510, 'blue': 0.9451}
# #fff2cc
_YELLOW = {'red': 1.0, 'green': 0.9490, 'blue': 0.8}
# #d9ead3
_GREEN  = {'red': 0.8510, 'green': 0.9176, 'blue': 0.8275}
# #f4cccc (light red for conditional formatting)
_RED    = {'red': 0.9569, 'green': 0.8, 'blue': 0.8}

# (header text, background color, column width in pixels)
MICROCOPY_HEADERS = [
    ('Location',             _BLUE,   150),
    ('Element',              _GRAY,   150),
    ('Current',              _YELLOW, 300),
    ('New',                  _GREEN,  350),
    ('Notes',                _GRAY,   350),
    ('Questions/Comments',   _GRAY,   300),
    ('QA',                   _GRAY,   120),
]

HEADER_ROW_HEIGHT = 50   # pixels

CELL_TEXT_FORMAT          = {'fontFamily': 'Calibri', 'fontSize': 11}
CELL_VERTICAL_ALIGNMENT   = 'MIDDLE'
CELL_HORIZONTAL_ALIGNMENT = 'LEFT'
CELL_WRAP_STRATEGY        = 'WRAP'

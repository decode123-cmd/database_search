"""Rebuild static/img/fig_v2.png from the original architecture figure (static/img/fig.png).

Changes made to the original: the database cylinder is labelled with the site name, the counts in the "Data" box come from the
workbook, and a "Software stack" band is added at the bottom. Needs Pillow, pandas and openpyxl:

    python scripts/make_architecture_figure.py [--file Final_akshat.xlsx] [--name CancerImmunoDB]
"""
import argparse
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from database import importer  # noqa: E402

SRC = os.path.join(ROOT, 'static', 'img', 'fig.png')
OUT = os.path.join(ROOT, 'static', 'img', 'fig_v2.png')
BOLD = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
REG = '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
NAVY, STEEL, PILL, PANEL = (5, 38, 89), (84, 130, 179), (42, 42, 104), (225, 240, 252)
BAND = 1200

# where the original draws its six "Data" lines (measured on fig.png): text starts at x=165, first baseline y=1474, pitch 78
DATA_BOX = {'clear': (150, 1415, 960, 1885), 'x': 165, 'first_baseline': 1474, 'pitch': 78, 'size': 66}

STACK = [
    ('Data tier', ['PostgreSQL', 'one table per', 'study type']),
    ('Application tier', ['Python 3.10', 'Django 5.0', 'Gunicorn']),
    ('Cheminformatics', ['RDKit 2023.03', '2D and 3D similarity', 'MACCS keys', 'Substructure search']),
    ('Web tier', ['HTML, CSS and', 'JavaScript', 'REST API (JSON, CSV)']),
]


def data_lines(tables):
    index = tables[importer.INDEX_TABLE]
    return [
        f"Animal Studies - {len(tables[importer.STUDY_TABLES['animal_studies']])}",
        f"Cell Line Studies - {len(tables[importer.STUDY_TABLES['cell_line']])}",
        f"Patient Studies - {len(tables[importer.STUDY_TABLES['patient_studies']])}",
        f"Techniques / Assays - {int(index['Controlled_Technique'].notna().sum())}",
        f"Cancer Type - {int(index['Cancer_Type'].notna().sum())}",
        f"Drug Type - {int(index['Drug_category'].notna().sum())}",
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--file', default=os.path.join(ROOT, 'Final_akshat.xlsx'))
    parser.add_argument('--name', default='CancerImmunoDB')
    args = parser.parse_args()
    tables, _ = importer.read_workbook(args.file)

    src = Image.open(SRC).convert('RGB')
    width, height = src.size
    fig = Image.new('RGB', (width, height + BAND), 'white')
    fig.paste(src, (0, 0))
    d = ImageDraw.Draw(fig)

    # the "Data" box counts
    left, top, right, bottom = DATA_BOX['clear']
    d.rectangle((left, top, right, bottom), fill=STEEL)
    font = ImageFont.truetype(BOLD, DATA_BOX['size'])
    for i, line in enumerate(data_lines(tables)):
        d.text((DATA_BOX['x'], DATA_BOX['first_baseline'] + i * DATA_BOX['pitch']), line, font=font, fill='white', anchor='ls')

    # the database cylinder carries the site name
    d.rectangle((1650, 1700, 2190, 1830), fill=NAVY)
    d.text((1922, 1762), args.name, font=ImageFont.truetype(BOLD, 80), fill='white', anchor='mm')

    # software stack band
    band_top = height + 170
    d.rounded_rectangle((80, band_top, width - 80, height + BAND - 50), radius=70, fill=PANEL)
    pill_w, pill_h, c = 1300, 170, 70
    px, py = (width - pill_w) // 2, band_top - 85
    d.polygon([(px + c, py), (px + pill_w - c, py), (px + pill_w, py + pill_h // 2), (px + pill_w - c, py + pill_h), (px + c, py + pill_h),
               (px, py + pill_h // 2)], fill=PILL)
    d.text((width / 2, py + pill_h / 2), 'Software stack', font=ImageFont.truetype(BOLD, 96), fill='white', anchor='mm')
    gap, margin = 70, 170
    box_w = (width - 2 * margin - gap * (len(STACK) - 1)) // len(STACK)
    y0, y1 = py + pill_h + 100, height + BAND - 130
    head, body = ImageFont.truetype(BOLD, 92), ImageFont.truetype(REG, 72)
    for i, (title, lines) in enumerate(STACK):
        x0 = margin + i * (box_w + gap)
        d.rounded_rectangle((x0, y0, x0 + box_w, y1), radius=60, fill=STEEL)
        d.text((x0 + 50, y0 + 105), title, font=head, fill='white', anchor='lm')
        d.line((x0 + 50, y0 + 185, x0 + box_w - 50, y0 + 185), fill=NAVY, width=7)
        for j, line in enumerate(lines):
            assert d.textlength(line, font=body) <= box_w - 100, line
            d.text((x0 + 50, y0 + 285 + j * 105), line, font=body, fill='white', anchor='lm')

    fig.save(OUT, optimize=True)
    mirror = os.path.join(ROOT, 'staticfiles', 'img', 'fig_v2.png')
    if os.path.isdir(os.path.dirname(mirror)):
        shutil.copyfile(OUT, mirror)
    print('saved', OUT, fig.size)
    print('Data box:', ' | '.join(data_lines(tables)))


if __name__ == '__main__':
    main()

"""Draw the statistics charts shown on the site from the data workbook.

The counts come from the same code as the Browse pages, so a chart can never disagree with its table.
Needs pandas, openpyxl, matplotlib and the project's `database` package:

    python scripts/make_stats_charts.py [--file Final_akshat.xlsx]

It writes static/img/stats_*.png and copies them to staticfiles/img/.
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib  # noqa: E402

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

from database import importer  # noqa: E402
from database.all_search_count import browse_frames  # noqa: E402

COLORS = (('Cell_Count', 'Cell line studies', '#1f4ed8'), ('Animal_Count', 'Animal studies', '#f59e0b'), ('Patient_Count', 'Patient studies', '#16a34a'))
CHARTS = [
    ('stats_technique.png', 'technique', 'Studies by assay or technique', None),
    ('stats_cancer_type.png', 'cancer_type', 'Studies by cancer type', None),
    ('stats_drug_category.png', 'drug_category', 'Studies by drug category', None),
    ('stats_immune_terms.png', 'immune', 'Most reported immune terms (top 25)', 25),
]
NOTES = {
    'technique': 'A study is counted under every technique it lists.',
    'immune': 'A study is counted under every immune term it lists, in any outcome.',
    'cancer_type': 'Each study is counted once.',
    'drug_category': 'Each study is counted once.',
}


def draw(result, kind, title, path, top):
    rows = sorted(result['table'].items(), key=lambda item: -sum(item[1].values()))
    if top:
        rows = rows[:top]
    names = [name for name, _ in rows]
    fig, ax = plt.subplots(figsize=(20, 10.5))
    bottom = [0] * len(names)
    for key, label, color in COLORS:
        values = [counts[key] for _, counts in rows]
        ax.bar(names, values, bottom=bottom, label=label, color=color, width=0.65)
        bottom = [b + v for b, v in zip(bottom, values)]
    ax.set_ylabel('Number of studies', fontsize=14)
    ax.set_title(title, fontsize=18, pad=14)
    ax.legend(fontsize=13)
    ax.margins(x=0.01)
    plt.xticks(rotation=90, fontsize=12)
    left_out = sum(result['unassigned'].values())
    note = NOTES[kind] + (f' {left_out} of {sum(result["totals"].values())} studies have no value from the list and are not shown.' if left_out else '')
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.text(0.01, 0.01, note, fontsize=12, color='#444444')
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--file', default=os.path.join(ROOT, 'Final_akshat.xlsx'))
    args = parser.parse_args()
    tables, _ = importer.read_workbook(args.file)
    studies = {'Cell_Count': tables['Browse_by_cell_line'], 'Animal_Count': tables['Browse_by_animal_studies'],
               'Patient_Count': tables['Browse_by_Patient_Studies']}
    for filename, kind, title, top in CHARTS:
        result = browse_frames(studies, tables['Browse_by_index'], kind)
        path = os.path.join(ROOT, 'static', 'img', filename)
        draw(result, kind, title, path, top)
        mirror = os.path.join(ROOT, 'staticfiles', 'img', filename)
        if os.path.isdir(os.path.dirname(mirror)):
            shutil.copyfile(path, mirror)
        print(f'{filename}: {len(result["table"])} rows drawn' if not top else f'{filename}: top {top}')


if __name__ == '__main__':
    main()

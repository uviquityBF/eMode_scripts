"""Checks for survey.py that don't need EMode. Run: python test_survey.py"""

import csv
import os
import tempfile

import survey


def test_append_rows_upgrades_header_without_misaligning_new_rows():
    # Regression test for a real bug (2026-10-05): adding a field to CROSS_FIELDS without also
    # widening the appending writer's fieldnames caused new rows to have fewer cells than the
    # (correctly upgraded) header -- silent under csv.DictWriter(extrasaction='ignore'), but every
    # later pd.read_csv() read the new rows' real data as NaN for the newly-added columns.
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'crossings.csv')
        survey.append_rows(path, ['a', 'b'], [{'a': 1, 'b': 2}])
        # a later run adds a field ('c') that the first write didn't know about
        survey.append_rows(path, ['a', 'b', 'c'], [{'a': 3, 'b': 4, 'c': 5}])
        with open(path, newline='') as f:
            rows = list(csv.DictReader(f))
        assert [len(r) for r in rows] == [3, 3], rows  # every row has one cell per header column
        assert rows[0] == {'a': '1', 'b': '2', 'c': ''}
        assert rows[1] == {'a': '3', 'b': '4', 'c': '5'}
        print("append_rows OK: header upgraded and new rows stay aligned with it")


if __name__ == '__main__':
    test_append_rows_upgrades_header_without_misaligning_new_rows()
    print('all passed')

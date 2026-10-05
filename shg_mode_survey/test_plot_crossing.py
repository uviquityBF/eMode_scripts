"""Checks for plot_crossing.py that don't need EMode. Run: python test_plot_crossing.py"""

import plot_crossing as pc


def test_safe_label_strips_question_mark():
    # '?' (hybrid/ambiguous mode label) is invalid in a Windows filename -- caught 2026-10-05
    # when plot_crossing.py crashed (OSError) on a run whose top crossings included one.
    assert pc.safe_label('TM165?') == 'TM165h'
    assert pc.safe_label('TM05') == 'TM05'  # unaffected when there's nothing to strip
    print("safe_label OK: 'TM165?' -> 'TM165h', 'TM05' unchanged")


if __name__ == '__main__':
    test_safe_label_strips_question_mark()
    print('all passed')

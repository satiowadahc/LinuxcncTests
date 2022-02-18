#! /usr/bin/python3
"""
 test_status.py Testing Status in Linuxcnc
    Written by Chad A. Woitas
    
"""

from collections import namedtuple
from typing import List, Dict, Optional
import time
import inspect
import linuxcnc
import sys
import traceback

from lcnc import LcncWindow

# Seconds between tests
TEST_FREQ = 0.01
TEST_TIMEOUT = 1000
JOG_TIMEOUT = 2.0
MOTION_TIMEOUT = 15.0


def dict_compare(orig_stat, new_stat) ->[set, set, set, set]:
    """
    Compare two dictionaries with each other
    :param orig_stat: Original Stat Object to Compare
    :param new_stat: New Stat Object to compare
    """

    d1 = {}
    d2 = {}

    for key in dir(orig_stat):
        if "__" in key:
            continue
        if "poll" in key:
            continue
        d1[key] = getattr(orig_stat, key)
    for key in dir(new_stat):
        if "__" in key:
            continue
        if "poll" in key:
            continue
        d2[key] = getattr(new_stat, key)

    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())

    shared_keys = d1_keys.intersection(d2_keys)
    added = d2_keys - d1_keys
    removed = d1_keys - d2_keys
    modified = {o: (d1[o], d2[o]) for o in shared_keys if d1[o] != d2[o]}
    same = set(o for o in shared_keys if d1[o] == d2[o])
    return added, removed, modified, same


def test_code_base(qtbot):
    """
    Validate test code
    :param qtbot:
    :return:
    """
    stat = linuxcnc.stat()
    stat.poll()
    stat1 = linuxcnc.stat()
    stat1.poll()

    added, removed, modified, same = dict_compare(stat, stat1)
    assert len(added) == 0
    assert len(removed) == 0
    assert len(modified) == 0
    assert len(same) > 80  # TODO This could be defined better, its actually 86 at this moment?

    # Todo more tests


def test_estop(qtbot):
    """
    Test all estop functions
    Including Hal, and command
    """

    window_test = LcncWindow()
    window_test.show()
    qtbot.addWidget(window_test)
    qtbot.wait(TEST_TIMEOUT)
    print()  # New line for test printout

    com = linuxcnc.command()
    stat = linuxcnc.stat()
    stat.poll()
    stat1 = linuxcnc.stat()
    stat1.poll()

    groups = [[linuxcnc.STATE_ESTOP_RESET, 0, 0, 1, linuxcnc.STATE_ESTOP_RESET, 0],
              [linuxcnc.STATE_ESTOP, 0, 0, 3, linuxcnc.STATE_ESTOP, 1],
              [linuxcnc.STATE_ESTOP_RESET, 0, 0, 3, linuxcnc.STATE_ESTOP_RESET, 0],
              ]

    com.state(linuxcnc.STATE_ESTOP_RESET)
    qtbot.wait(TEST_TIMEOUT)
    stat1.poll()
    added, removed, modified, same = dict_compare(stat, stat1)
    assert len(added) == 0
    assert len(removed) == 0
    assert stat1.estop == 0

    for idx, check in enumerate(groups):
        print(f"Commanding {idx}")

        stat.poll()
        com.state(check[0])
        qtbot.wait(TEST_TIMEOUT)
        stat1.poll()
        added, removed, modified, same = dict_compare(stat, stat1)
        assert len(added) == check[1]
        assert len(removed) == check[2]
        assert len(modified) == check[3]
        assert stat1.task_state == check[4]
        assert stat1.estop == check[5]


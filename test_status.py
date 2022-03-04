#! /usr/bin/python3
"""
 test_status.py Testing Status in Linuxcnc
    Written by Chad A. Woitas
    
"""
import functools
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


def dict_compare(orig_stat, new_stat) -> [set, set, set, set]:
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


# TODO: validate
def set_estop_ready() -> bool:
    """
    Helper Function to enable the estop
    :return: True if successful
    """
    com = linuxcnc.command()
    stat = linuxcnc.stat()
    com.state(linuxcnc.STATE_ESTOP_RESET)
    time.sleep(0.1)  # TODO should this be a qtbot.wait call?
    stat.poll()
    return stat.estop == 0


# TODO: validate
def set_machine_enabled() -> bool:
    """
    Helper Function to enable the machine
    :return: True if successful
    """
    com = linuxcnc.command()
    stat = linuxcnc.stat()
    com.state(linuxcnc.STATE_ON)
    time.sleep(0.1)  # TODO should this be a qtbot.wait call?
    stat.poll()
    return stat.task_state == linuxcnc.STATE_ON


def test_code_base():
    """
    Validate test code
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

    # TODO: Test poll somewhere in here?


def initialize_test(func):
    """
    Decorator to set up test state
    :param func: Test function to call after
    :return: Test initialized function
    """
    @functools.wraps(func)
    def wrapper(**kwargs):

        window_test = LcncWindow()
        window_test.show()
        kwargs["qtbot"].addWidget(window_test)
        kwargs["qtbot"].wait(TEST_TIMEOUT)
        print()  # New line for test printout
        func(**kwargs)

    return wrapper


@initialize_test
def requires_machine_enabled(func):
    """
    Decorator to enable the machine before a test
    :param func:
    :return:
    """
    def wrapper(**kwargs):
        t_com = linuxcnc.command()
        t_com.state(linuxcnc.STATE_ESTOP_RESET)
        t_com.state(linuxcnc.STATE_ON)
        print()  # New line for test printout

        func(**kwargs)

    return wrapper

@initialize_test
def test_estop(qtbot):
    """
    Test all estop functions
    Including Hal, and command
    :param qtbot: Test Suite Control for pytest-qt
    """

    # TODO add external estop commands here, amp-fault, misc-error

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


@initialize_test
def test_machine_enable(qtbot):
    """
    Test all machine enable functions
    Including Hal, and command
    :param qtbot: Test Suite Control for pytest-qt
    """
    assert set_estop_ready()
    com = linuxcnc.command()
    stat = linuxcnc.stat()
    stat.poll()
    stat1 = linuxcnc.stat()
    stat1.poll()

    #          COMMAND, ADDED, REMOVED, MODIFIED, TASKSTATE, ESTOP
    groups = [[linuxcnc.STATE_ON, 0, 0, 5, linuxcnc.STATE_ON, 0],
              [linuxcnc.STATE_OFF, 0, 0, 3, linuxcnc.STATE_OFF, 1],
              [linuxcnc.STATE_ON, 0, 0, 3, linuxcnc.STATE_ON, 1],
              ]
    for idx, check in enumerate(groups):
        print(f"Commanding {idx}")

        stat.poll()
        com.state(check[0])
        qtbot.wait(TEST_TIMEOUT)
        stat1.poll()
        added, removed, modified, same = dict_compare(stat, stat1)
        print(modified)
        assert len(added) == check[1]
        assert len(removed) == check[2]
        assert len(modified) == check[3]
        assert stat1.task_state == check[4]
        assert stat1.estop == check[5]


# def test_acceleration(qtbot):
#     """
#         acceleration
#             (returns float) - default acceleration, reflects the ini entry [TRAJ]DEFAULT_ACCELERATION.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_active_queue(qtbot):
#     """
#
#     (returns integer) - number of motions blending.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#
# def test_actual_position(qtbot):
#     """
#
#     (returns tuple of floats) - current trajectory position, (x y z a b c u v w) in machine units.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#
# def test_adaptive_feed_enabled(qtbot):
#     """
#
#     (returns boolean) - status of adaptive feedrate override (0/1).
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#
# def test_ain(qtbot):
#     """
#
#     (returns tuple of floats) - current value of the analog input pins.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#
# def test_angular_units(qtbot):
#     """
#
#     (returns float) - machine angular units per deg, reflects [TRAJ]ANGULAR_UNITS ini value.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_aout(qtbot):
#     """
#
#     (returns tuple of floats) - current value of the analog output pins.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_axes(qtbot):
#     """
#
#     (returns integer) - number of axes. Derived from [TRAJ]COORDINATES ini value.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_axis(qtbot):
#     """
#
#     (returns tuple of dicts) - reflecting current axis values. See The axis dictionary.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_axis_mask(qtbot):
#     """
#
#     (returns integer) - mask of axis available as defined by [TRAJ]COORDINATES in the ini file. Returns the sum of the axes X=1, Y=2, Z=4, A=8, B=16, C=32, U=64, V=128, W=256.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_block_delete(qtbot):
#     """
#
#     (returns boolean) - block delete curren status.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_command(qtbot):
#     """
#
#     (returns string) - currently executing command.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_current_line(qtbot):
#     """
#
#     (returns integer) - currently executing line, int.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_current_vel(qtbot):
#     """
#
#     (returns float) - current velocity in user units per second.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_cycle_time(qtbot):
#     """
#
#     (returns float) - thread period
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_debug(qtbot):
#     """
#
#     (returns integer) - debug flag from the ini file.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_delay_left(qtbot):
#     """
#
#     (returns float) - remaining time on dwell (G4) command, seconds.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_din(qtbot):
#     """
#
#     (returns tuple of integers) - current value of the digital input pins.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_distance_to_go(qtbot):
#     """
#
#     (returns float) - remaining distance of current move, as reported by trajectory planner.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_dout(qtbot):
#     """
#
#     (returns tuple of integers) - current value of the digital output pins.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_dtg(qtbot):
#     """
#
#     (returns tuple of floats) - remaining distance of current move for each axis, as reported by trajectory planner.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_echo_serial_number(qtbot):
#     """
#
#     (returns integer) - The serial number of the last completed command sent by a UI to task.
#      All commands carry a serial number. Once the command has been executed, its serial number
#       is reflected in echo_serial_number.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_enabled(qtbot):
#     """
#
#     (returns boolean) - trajectory planner enabled flag.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
# # Tested first
# # def test_estop(qtbot):
# #     """
# #
# #     (returns integer) - Returns either STATE_ESTOP or not.
# #     """
# #     window_test = LcncWindow()
# #     window_test.show()
# #     qtbot.addWidget(window_test)
# #     qtbot.wait(TEST_TIMEOUT)
# #     print()  # New line for test printout
# #
# #     assert set_estop_ready()
# #     assert set_machine_enabled()
# #
# #     # TODO
#
#
# def test_exec_state(qtbot):
#     """
#
#     (returns integer) - task execution state. One of EXEC_ERROR, EXEC_DONE, EXEC_WAITING_FOR_MOTION,
#     EXEC_WAITING_FOR_MOTION_QUEUE, EXEC_WAITING_FOR_IO, EXEC_WAITING_FOR_MOTION_AND_IO,
#     EXEC_WAITING_FOR_DELAY, EXEC_WAITING_FOR_SYSTEM_CMD, EXEC_WAITING_FOR_SPINDLE_ORIENTED.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_feed_hold_enabled(qtbot):
#     """
#
#     (returns boolean) - enable flag for feed hold.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_feed_override_enabled(qtbot):
#     """
#
#     (returns boolean) - enable flag for feed override.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_feedrate(qtbot):
#     """
#
#     (returns float) - current feedrate override, 1.0 = 100%.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_file(qtbot):
#     """
#
#     (returns string) - currently loaded gcode filename with path.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_flood(qtbot):
#     """
#
#     (returns integer) - Flood status, either FLOOD_OFF or FLOOD_ON.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_g5x_index(qtbot):
#     """
#
#     (returns integer) - currently active coordinate system, G54=1, G55=2 etc.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_g5x_offset(qtbot):
#     """
#
#     (returns tuple of floats) - offset of the currently active coordinate system.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_g92_offset(qtbot):
#     """
#
#     (returns tuple of floats) - pose of the current g92 offset.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_gcodes(qtbot):
#     """
#
#     (returns tuple of integers) - Active G-codes for each modal group.
#     G code constants G_0, G_1, G_2, G_3, G_4, G_5, G_5_1, G_5_2, G_5_3, G_7, G_8, G_100,
#     G_17, G_17_1, G_18, G_18_1, G_19, G_19_1, G_20, G_21, G_28, G_28_1, G_30, G_30_1, G_33,
#     G_33_1, G_38_2, G_38_3, G_38_4, G_38_5, G_40, G_41, G_41_1, G_42, G_42_1, G_43, G_43_1,
#     G_43_2, G_49, G_50, G_51, G_53, G_54, G_55, G_56, G_57, G_58, G_59, G_59_1, G_59_2,
#     G_59_3, G_61, G_61_1, G_64, G_73, G_76, G_80, G_81, G_82, G_83, G_84, G_85, G_86, G_87,
#     G_88, G_89, G_90, G_90_1, G_91, G_91_1, G_92, G_92_1, G_92_2, G_92_3, G_93, G_94, G_95,
#     G_96, G_97, G_98, G_99
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_homed(qtbot):
#     """
#
#     (returns tuple of integers) - currently homed joints, 0 = not homed, 1 = homed.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_id(qtbot):
#     """
#     (returns integer) - currently executing motion id.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_inpos(qtbot):
#     """
#
#     (returns boolean) - machine-in-position flag.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_input_timeout(qtbot):
#     """
#
#     (returns boolean) - flag for M66 timer in progress.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_interp_state(qtbot):
#     """
#
#     (returns integer) - current state of RS274NGC interpreter. One of INTERP_IDLE, INTERP_READING, INTERP_PAUSED, INTERP_WAITING.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_interpreter_errcode(qtbot):
#     """
#
#     (returns integer) - current RS274NGC interpreter return code. One of
#     INTERP_OK, INTERP_EXIT, INTERP_EXECUTE_FINISH, INTERP_ENDFILE, INTERP_FILE_NOT_OPEN,
#      INTERP_ERROR.
#       see src/emc/nml_intf/interp_return.hh
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_joint(qtbot):
#     """
#
#     (returns tuple of dicts) - reflecting current joint values. See The joint dictionary.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_joint_actual_position(qtbot):
#     """
#
#     (returns tuple of floats) - actual joint positions.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_joint_position(qtbot):
#     """
#
#     (returns tuple of floats) - Desired joint positions.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_joints(qtbot):
#     """
#
#     (returns integer) - number of joints. Reflects [KINS]JOINTS ini value.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_kinematics_type(qtbot):
#     """
#
#     (returns integer) - The type of kinematics. One of:
#
#         KINEMATICS_IDENTITY
#
#         KINEMATICS_FORWARD_ONLY
#
#         KINEMATICS_INVERSE_ONLY
#
#         KINEMATICS_BOTH
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
#
# def test_limit(qtbot):
#     """
#
#     (returns tuple of integers) - axis limit masks. minHardLimit=1, maxHardLimit=2, minSoftLimit=4, maxSoftLimit=8.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_linear_units(qtbot):
#     """
#
#     (returns float) - machine linear units per mm, reflects [TRAJ]LINEAR_UNITS ini value.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_lube(qtbot):
#     """
# (returns integer) - lube on flag.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_lube_level(qtbot):
#     """
#
# (returns integer) - reflects iocontrol.0.lube_level.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_max_acceleration(qtbot):
#     """
#
# (returns float) - maximum acceleration. Reflects [TRAJ]MAX_ACCELERATION.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_max_velocity(qtbot):
#     """
#
# (returns float) - maximum velocity. Reflects the current maximum velocity.
#  If not modified by halui.max-velocity or similar it should reflect [TRAJ]MAX_VELOCITY.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_mcodes(qtbot):
#     """
#
# (returns tuple of 10 integers) - currently active M-codes.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_mist(qtbot):
#     """
#
# (returns integer) - Mist status, either MIST_OFF or MIST_ON
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_motion_line(qtbot):
#     """
#
# (returns integer) - source line number motion is currently executing. Relation to id unclear.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_motion_mode(qtbot):
#     """
#
# (returns integer) - This is the mode of the Motion controller. One of TRAJ_MODE_COORD, TRAJ_MODE_FREE, TRAJ_MODE_TELEOP
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
# def test_motion_type(qtbot):
#     """
#
# (returns integer) - The type of the currently executing motion. One of:
#
#     MOTION_TYPE_TRAVERSE
#
#     MOTION_TYPE_FEED
#
#     MOTION_TYPE_ARC
#
#     MOTION_TYPE_TOOLCHANGE
#
#     MOTION_TYPE_PROBING
#
#     MOTION_TYPE_INDEXROTARY
#
#     Or 0 if no motion is currently taking place.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
#
# def test_optional_stop(qtbot):
#     """
#
# (returns integer) - option stop flag.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_paused(qtbot):
#     """
#
# (returns boolean) - motion paused flag.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_pocket_prepped(qtbot):
#     """
#
# (returns integer) - A Tx command completed, and this pocket is prepared. -1 if no prepared pocket.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
# # I think this needs to be tested really early...
# def test_poll(qtbot):
#     """
#
# -(built-in function) method to update current status attributes.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_position(qtbot):
#     """
#
# (returns tuple of floats) - trajectory position.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_probe_tripped(qtbot):
#     """
#
# (returns boolean) - flag, True if probe has tripped (latch)
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_probe_val(qtbot):
#     """
#
# (returns integer) - reflects value of the motion.probe-input pin.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_probed_position(qtbot):
#     """
#
# (returns tuple of floats) - position where probe tripped.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_probing(qtbot):
#     """
#
# (returns boolean) - flag, True if a probe operation is in progress.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_program_units(qtbot):
#     """
#
# (returns integer) - one of CANON_UNITS_INCHES=1, CANON_UNITS_MM=2, CANON_UNITS_CM=3
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_queue(qtbot):
#     """
#
# (returns integer) - current size of the trajectory planner queue.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_queue_full(qtbot):
#     """
#
# (returns boolean) - the trajectory planner queue is full.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_rapidrate(qtbot):
#     """
#
# (returns float) - rapid override scale.
#
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_read_line(qtbot):
#     """
#
# (returns integer) - line the RS274NGC interpreter is currently reading.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_rotation_xy(qtbot):
#     """
#
# (returns float) - current XY rotation angle around Z axis.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_settings(qtbot):
#     """
#
# (returns tuple of floats) - current interpreter settings. settings[0] = sequence number, settings[1] = feed rate, settings[2] = speed.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_spindle(qtbot):
#     """
#
# ' (returns tuple of dicts) ' - returns the current spindle status see <sec:the-spindle-dictionary, The spindle dictionary>>
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_spindles(qtbot):
#     """
#
# (returns integer) - number of spindles. Reflects [TRAJ]SPINDLES ini value.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_state(qtbot):
#     """
#
# (returns integer) - current command execution status. One of RCS_DONE, RCS_EXEC, RCS_ERROR.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_task_mode(qtbot):
#     """
#
# (returns integer) - current task mode. one of MODE_MDI, MODE_AUTO, MODE_MANUAL.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_task_paused(qtbot):
#     """
#
# (returns integer) - task paused flag.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_task_state(qtbot):
#     """
#
# (returns integer) - current task state. one of STATE_ESTOP, STATE_ESTOP_RESET, STATE_ON, STATE_OFF.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_tool_in_spindle(qtbot):
#     """
#
# (returns integer) - current tool number.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_tool_offset(qtbot):
#     """
#
# (returns tuple of floats) - offset values of the current tool.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
# def test_tool_table(qtbot):
#     """
#
# (returns tuple of tool_results) - list of tool entries. Each entry is a sequence of the following fields:
# id,
# xoffset, yoffset, zoffset,
# aoffset, boffset, coffset,
#  uoffset, voffset, woffset,
#   diameter, frontangle, backangle, orientation.
#   The id and orientation are integers and the rest are floats.
#     """
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#
#
#
# def velocity(qtbot):
#     """
#
# (returns float) - This property is defined, but it does not have a useful interpretation.
#
#     """
#
#     window_test = LcncWindow()
#     window_test.show()
#     qtbot.addWidget(window_test)
#     qtbot.wait(TEST_TIMEOUT)
#     print()  # New line for test printout
#
#     assert set_estop_ready()
#     assert set_machine_enabled()
#
#     # TODO
#

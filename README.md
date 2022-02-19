# Linuxcnc Status Tests

Dependencies: Linuxcnc, pytest, pytest-qt, python3-pyqt5

Current Use:
  - run Linuxcnc in a separate process
  - pytest test_status.py

## Roadmap - Things to do yet 
  - Fill in tests 
  - Find a solution for headless or non-headless
  - Add hal commands to validate status
  - Create stub test suite for command. - Currently unplanned
  - Get some pylint validation somewhere in here, possibly black
  - CI testing for a test suite
  - Integrate this into Linuxcnc repository.
  
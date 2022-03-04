#! /usr/bin/python3
"""
Basic Display to Keep linuxcnc running while testing status

Install in path and change to executable
"""

import sys
import time

if __name__ == "__main__":
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)

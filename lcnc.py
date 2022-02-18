"""
  lcnc.py - Qt5 Window for monitoring Linuxcnc Status

  Written by Chad A. Woitas AKA satiowadahc

"""

from typing import Optional

from PyQt5 import QtCore, QtWidgets
from lcnc_window_ui import Ui_lcnc_test_window
import sys

import linuxcnc

# fmt: off
GCODES = { "0": "G0", "10": "G1", "20": "G2",
           "30": "G3", "40": "G4", "50": "G5",
           "51": "G5.1", "52": "G5.2", "53": "G5.3",
           "70": "G7", "80": "G8", "100": "G10",
           "170": "G17", "171": "G17.1", "180": "G18",
           "181": "G18.1", "190": "G19", "191": "G19.1",
           "200": "G20", "210": "G21", "280": "G28",
           "281": "G28.1", "300": "G30", "301": "G30.1",
           "330": "G33", "331": "G33.1", "382": "G38.2",
           "383": "G38.3", "384": "G38.4", "385": "G38.5",
           "400": "G40", "410": "G41", "411": "G41.1",
           "420": "G42", "421": "G42.1", "430": "G43",
           "431": "G43.1", "432": "G43.2", "490": "G49",
           "500": "G50", "510": "G51", "530": "G53",
           "540": "G54", "550": "G55", "560": "G56",
           "570": "G57", "580": "G58", "590": "G59",
           "591": "G59.1", "592": "G59.2", "593": "G59.3",
           "610": "G61", "611": "G61.1", "640": "G64",
           "730": "G73", "760": "G76", "800": "G80",
           "810": "G81", "820": "G82", "830": "G83",
           "840": "G84", "850": "G85", "860": "G86",
           "870": "G87", "880": "G88", "890": "G89",
           "900": "G90", "901": "G90.1", "910": "G91",
           "911": "G91.1", "920": "G92", "921": "G92.1",
           "922": "G92.2", "923": "G92.3", "930": "G93",
           "940": "G94", "950": "G95", "960": "G96",
           "970": "G97", "980": "G98", "990": "G99",
           "-1": "?"
}
# fmt: on


class LcncWindow(QtWidgets.QMainWindow):
    """Main Window class for testing linuxcnc"""
    def __init__(self, parent=None):
        super().__init__()

        self.ui = Ui_lcnc_test_window()
        self.ui.setupUi(self)

        self.status_labels = []
        self.code_labels = []
        for i in range(30):
            self.ui.verticalLayout.addLayout(self.create_line(" "))

        self.status = linuxcnc.stat()
        self.command = linuxcnc.command()

        self.cyclic_timer = QtCore.QTimer()
        self.cyclic_timer.timeout.connect(self.periodic)
        self.cyclic_timer.setInterval(500)
        self.cyclic_timer.start()

        self.is_running = True

    def periodic(self):
        """Fetch Information and update the display"""

        try:
            self.status.poll()

            if not self.is_running:
                print("Linuxcnc detected")
            self.is_running = True
        except Exception as e:
            print(e)
            if self.is_running:
                self.is_running = False
                print("Linuxcnc Not Detected")

        if self.is_running:
            try:
                self.load_table()
            except Exception as e:
                print(e)

    def load_table(self):
        """Parse Gcodes and add them to the table"""
        current_codes = list(self.status.gcodes)

        self.ui.verticalLayout.update()

        for idx, code in enumerate(current_codes):
            if idx < len(self.status_labels):
                if f"{code}" in GCODES.keys():
                    self.status_labels[idx].setText(f"{GCODES[f'{code}']}")
                    self.code_labels[idx].setText(f"{code}")
                else:
                    self.status_labels[idx].setText(f" - ")
                    self.code_labels[idx].setText(f"{code}")

        for idx, code in enumerate(list(self.status.mcodes)):
            if idx + len(current_codes) + 1 < len(self.status_labels):
                if code >= 0:
                    self.status_labels[idx + len(current_codes) + 1].setText(f"M{code}")
                    self.code_labels[idx + len(current_codes) + 1].setText(f"{code}")
                else:
                    self.status_labels[idx + len(current_codes) + 1].setText(f"-")
                    self.code_labels[idx + len(current_codes) + 1].setText(f"{code}")

    def create_line(self, code):
        """
        Create two labels in a box to hold information
        :param code: Integer Value from status
        """
        layout = QtWidgets.QHBoxLayout()
        layout.setObjectName(f"layout{code}")

        codelabel = QtWidgets.QLabel(self.ui.centralwidget)
        codelabel.setObjectName(f"codeLabel{code}")
        codelabel.setText(f"{code}")
        layout.addWidget(codelabel)
        self.code_labels.append(codelabel)

        humanlabel = QtWidgets.QLabel(self.ui.centralwidget)
        humanlabel.setObjectName(f"humanLabel{code}")
        layout.addWidget(humanlabel)
        self.status_labels.append(humanlabel)

        return layout


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    lcnc = LcncWindow()
    lcnc.show()
    sys.exit(app.exec_())

#!/usr/bin/python
# -*- coding: UTF-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys, time

from thdec import ThDec, closeAll


MAX = 100
BAR_COUNT = 5
SLEEP = 0.05
class MainFrame(QFrame):
	def __init__(self):
		QFrame.__init__(self)

		self._threads = []

		layout = QVBoxLayout(self)

		self.barList = []
		for i in range(BAR_COUNT):
			bar = QProgressBar(self)
			bar.setRange(0, MAX)
			layout.addWidget(bar)
			self.barList.append(bar)

		bLayout = QHBoxLayout()
		layout.addLayout(bLayout)

		goButton = QPushButton('Go', self)
		goButton.clicked.connect(self.goClick)
		bLayout.addWidget(goButton)

		stopButton = QPushButton('Stop', self)
		stopButton.clicked.connect(self.stopClick)
		bLayout.addWidget(stopButton)

	def goClick(self):
		closeAll()
		for i in range(BAR_COUNT):
			thr = self.go(i, thdec_start = True)
			self._threads.append(thr)

	def stopClick(self):
		for thr in self._threads:
			thr.stop()
		self._threads = []

	@ThDec
	def go(self, barNum):
		for progress in range(MAX+1):
			if self.isStopped():
				break
			self.setProgress(barNum, progress, thdec_method = 'q')
			time.sleep(SLEEP)

	def setProgress(self, barNum, progress):
		self.barList[barNum].setValue(progress)

	def closeEvent(self, event):
		closeAll()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	mainFrame = MainFrame()
	mainFrame.show()
	app.exec_()


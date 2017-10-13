# -*- coding: UTF-8 -*-


"""ThDec - Simple Python QThread decorator"""


from PyQt4.QtCore import *
import collections


threads = []


class Thread__(QThread):
	global threads
	ACTION_SETATTR = 0
	ACTION_CALL    = 1
	ACTION_GETLIST = 2
	ACTION_GETDICT = 3
	def __init__(self, func):
		QThread.__init__(self)

		self.thdec_func = func
		self.thdec_stopFlag = False

		self.connect(self, SIGNAL('fromMainThread(PyQt_PyObject, PyQt_PyObject)'),
						self._fromMainThread, Qt.QueuedConnection)
		self.connect(self, SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
						self._fromMainThread, Qt.BlockingQueuedConnection)
		self.connect(self, SIGNAL('finished()'), self._removeThread)

	def run(self):
		self.thdec_func(self, *self.thdec_args)

	def __call__(self, instance, *args, **kwargs):
		self.thdec_instance = instance
		self.thdec_args = args

		if kwargs.get('thdec_start'):
			self.start()

	def __getattr__(self, name):
		if name.startswith('thdec_'):
			print name
			return self.__dict__[name]

		attr = self.thdec_instance.__getattribute__(name)
		if callable(attr):
			self.thdec_lastCallFunc = self.thdec_instance.__class__.__dict__[name]
			return self._callFunc
		elif type(attr) in (list, dict):
			self.emit(SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
						self.ACTION_GETLIST if type(attr) == list else self.ACTION_GETDICT,
						name)
			return self.thdec_result
		elif isinstance(attr, collections.Hashable):
			return attr
		else:
			raise(TypeError('unhashable type: %s' % type(attr).__name__))

	def __setattr__(self, name, value):
		if name.startswith('thdec_'):
			self.__dict__[name] = value
		else:
			self.thdec_instance.__setattr__(name, value)
			self.emit(SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'), self.ACTION_SETATTR, (name, value))

	def _callFunc(self, *args, **kwargs):
		method = kwargs.get('thdec_method')
		if not method:
			return self.thdec_lastCallFunc(self, *args)
		if method == 'q':
			self.emit(SIGNAL('fromMainThread(PyQt_PyObject, PyQt_PyObject)'),
						self.ACTION_CALL, (self.thdec_lastCallFunc, args))
			return
		if method == 'b':
			self.emit(SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
						self.ACTION_CALL, (self.thdec_lastCallFunc, args))
			return self.thdec_result
		raise Exception('Unknown thdec_method == "%s"' % method)

	def _fromMainThread(self, action, value):
		if action == self.ACTION_SETATTR:
			self.thdec_instance.__setattr__(*value)
		elif action == self.ACTION_CALL:
			func, arg = value
			self.thdec_result = func(self.thdec_instance, *arg)
		elif action == self.ACTION_GETLIST:
			self.thdec_result = self.thdec_instance.__getattribute__(value)[:]
		elif action == self.ACTION_GETDICT:
			self.thdec_result = self.thdec_instance.__getattribute__(value).copy()

	def stop(self):
		self.disconnect(self, SIGNAL('fromMainThread(PyQt_PyObject, PyQt_PyObject)'), self._fromMainThread)
		self.disconnect(self, SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'), self._fromMainThread)
		self.thdec_stopFlag = True

	def isStopped(self):
		return self.thdec_stopFlag

	def _removeThread(self):
		threads.remove(self)

def ThDec(func):
	"""ThDec - Thread decorator

Exmaple:
class Foo(QLabel):
	def __init__(self, parent = None):
		QLabel.__init__(self, parent)
		self.setFixedSize(320, 240)
		self.digits = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']

	@ThDec
	def bar(self, primaryText):
		rows = []
		digits = self.digits
		for item in digits:
			rows.append('%s: %s' % (primaryText, item))
			self.setText('\n'.join(rows), thdec_method = 'b')
			sleep(0.5)

	def setText(self, text):
		QLabel.setText(self, text)


if __name__ == "__main__":
	app = QApplication(sys.argv)
	foo = Foo()
	foo.show()
	foo.bar('From thread', thdec_start = True)
	app.exec_()"""

	def wrapper(*args, **kwargs):
		global threads
		thread = Thread__(func)
		thread(*args, **kwargs)
		threads.append(thread)
		return thread
	return wrapper

def closeAll():
	"""Close all threads"""
	for thread in threads:
		thread.stop()
	for thread in threads:
		thread.wait()

def terminateAll():
	"""Terminate all threads"""
	for thread in threads[:]:
		thread.terminate()

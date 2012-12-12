"""Provides an API wrapper around the Firmata wire protocol.

There are two major pieces to the firmata module. When FirmataInit() is called, a thread is spun up to handle serial
port IO. Its sole function is to read bytes into the read queue and write bytes from the write queue. These queues are
then used by the main body of code to respond to API calls made by the host application.

The API presented to the host program is encapsulated in the `Board` class, instances of which are obtained by calling
the previously mentioned `FirmataInit()` function. You can create as many Board classes as you wish, but you will not
go to space today if you create more than on on the same serial port.
"""

from Queue import Queue, Empty
import serial
import sys
import threading

from firmata.constants import *

IO_TIMEOUT = 0.2  # Number of seconds to block on IO. Set to None for infinite timeout.
BYTES_IN_CHUNK = 100

class _IOThread(threading.Thread):
  def __init__(self, port, baud, log=False):
    self._port = port
    self._baud = baud
    self.shutdown = False
    self.from_board = Queue()
    self.from_board_condition = threading.Condition()
    self.to_board = Queue()
    self._log = log
    super(_IOThread, self).__init__()

  def run(self):
    """Thread that communicates over the serial port.

    It operates by reading at most BYTES_IN_CHUNK bytes into the read queue, then writing at most BYTES_IN_CHUNK
    bytes from the write queue. Since it uses task_done() after each written byte, it's possible to .join() the
    write queue from the main thread to block until a write completes.
    """
    serial_port = serial.Serial(port=self._port, baudrate=self._baud, timeout=0.2)
    logfile = None
    if self._log:
      logfile = open('serial_log.txt', 'w')
    serial_port.flushInput()
    serial_port.flushOutput()
    while not self.shutdown:
      # The stuff with self.from_board_condition serves the purpose of notifying the main thread when there are things
      # to read, if the main thread was trying to block on reading these things.
      self.from_board_condition.acquire()
      r = serial_port.read(BYTES_IN_CHUNK)
      while len(r) != 0:
        [(self.from_board.put(ord(i)), logfile.write('<< %s (%s)\n' % (hex(ord(i)), CONST_R.get(ord(i), ''))) if self._log else None) for i in r]
        if self._log:
          logfile.flush()
        r = serial_port.read(BYTES_IN_CHUNK)
      self.from_board_condition.notifyAll()
      self.from_board_condition.release()
      bytes_written = 0
      while not self.to_board.empty() and bytes_written < BYTES_IN_CHUNK:
        try:
          w = self.to_board.get(block=False)
          (serial_port.write(chr(w)), logfile.write('>> %s (%s)\n' % (hex(w), CONST_R.get(w, ''))) if self._log else None)
          self.to_board.task_done()
          bytes_written += 1
        except Empty:
          break
    serial_port.close()
    logfile.close()

class Board(object):
  def __init__(self, port, baud, log=False, start_serial=False):
    """Board object constructor. Should not be called directly.

    Args:
      port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
      baud: A number representing the baud rate to use for serial communication.
      start_serial: If True, starts the serial IO thread right away. Default: False.
    """
    self._io_thread = _IOThread(port, baud, log=log)
    self._out = self._io_thread.to_board
    self._in = self._io_thread.from_board
    self._in_condition = self._io_thread.from_board_condition
    if start_serial:
      self._io_thread.start()

  def Init(self):
    """Start serial port communications, and configure ourselves by processing a capability query."""
    try:
      [self._out.put(i) for i in (CONST['SYSEX_START'], CONST['SE_CAPABILITY_QUERY'], CONST['SYSEX_END'])]
      self._out.join()
      while True:
        self._in_condition.acquire()  # In effect, this turns on cooperative multi-tasking with the IO thread.
        inp = None
        try:
          inp = self._in.get(block=False)
          print '%s (%s)' % (hex(inp), CONST_R.get(inp, ''))
        except Empty:
          self._in_condition.wait()
          continue
        self._in_condition.release()
    except:
      self._io_thread.shutdown = True
      self._io_thread.join()
      raise


def FirmataInit(port, baud=57600, log=False):
  """Instantiate a `Board` object for a given serial port.

  Args:
    port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
    baud: A number representing the baud rate to use for serial communication.

  Returns:
    A Board object which implements the firmata protocol over the specified serial port.
  """
  return Board(port, baud, log=log, start_serial=True)

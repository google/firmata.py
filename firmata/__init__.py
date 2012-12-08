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
import threading

from firmata.constants import *

IO_TIMEOUT = 0.2  # Number of seconds to block on IO. Set to None for infinite timeout.
BYTES_IN_CHUNK = 100

class _IOThread(threading.Thread):
  def __init__(self, port, baud):
    self._port = port
    self._baud = baud
    self.shutdown = False
    self.from_board = Queue()
    self.to_board = Queue()
    super(_IOThread, self).__init__()

  def run(self):
    serial_port = serial.Serial(port=self._port, baudrate=self._baud, timeout=0.2)
    while not self.shutdown:
      r = serial_port.read(BYTES_IN_CHUNK)
      [self.from_board.put(i) for i in r]
      bytes_written = 0
      while not self.to_board.empty() and bytes_written < BYTES_IN_CHUNK:
        try:
          w = self.to_board.get(block=False)
          serial_port.write(w)
          self.to_board.task_done()
          bytes_written += 1
        except Empty:
          break

class Board(object):
  def __init__(self, port, baud, start_serial=False):
    """Board object constructor. Should not be called directly.

    Args:
      port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
      baud: A number representing the baud rate to use for serial communication.
      start_serial: If True, starts the serial IO thread right away. Default: False.
    """
  self._io_thread = _IOThread(port, baud)
  if start_serial:
    self._io_thread.start()
  self._out = self._io_thread.to_board
  self._in = self._io_thread.from_board

def FirmataInit(port, baud=57600):
  """Instantiate a `Board` object for a given serial port.

  Args:
    port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
    baud: A number representing the baud rate to use for serial communication.

  Returns:
    A Board object which implements the firmata protocol over the specified serial port.
  """
  return Board(port, baud, start_serial=True)

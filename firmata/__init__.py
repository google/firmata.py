"""Provides an API wrapper around the Firmata wire protocol.

There are two major pieces to the firmata module. When FirmataInit() is called, a thread is spun up to handle serial
port IO. Its sole function is to read bytes into the read queue and write bytes from the write queue. These queues are
then used by the main body of code to respond to API calls made by the host application.

The API presented to the host program is encapsulated in the `Board` class, instances of which are obtained by calling
the previously mentioned `FirmataInit()` function. You can create as many Board classes as you wish, but you will not
go to space today if you create more than on on the same serial port.
"""

from Queue import Queue, Empty
import sys

from firmata.constants import *


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

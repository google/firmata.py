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
import threading

from firmata.constants import *
from firmata import io


class Board(threading.Thread):
  def __init__(self, port, baud, log_to_file=None, start_serial=False):
    """Board object constructor. Should not be called directly.

    Args:
      port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
      baud: A number representing the baud rate to use for serial communication.
      log_to_file: A string specifying the file to log serial events to, or None (the default) for no logging.
      start_serial: If True, starts the serial IO thread right away. Default: False.
    """
    self.port = io.SerialPort(port=port, baud=baud, log_to_file=log_to_file, start_serial=start_serial)
    self.shutdown = False

  def StartCommunications(self):
    self.port.StartCommunications()
    self.shutdown = False
    self.start()

  def StopCommunications(self):
    self.port.StopCommunications()
    self.shutdown = True
    self.join()

  def __del__(self):
    self.port.StopCommunications()

  def run(self):
    while not self.shutdown:
      try:
        self.port.reader.q.get(timeout=0.2)
      except Empty:
        pass


def FirmataInit(port, baud=57600, log_to_file=None):
  """Instantiate a `Board` object for a given serial port.

  Args:
    port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
    baud: A number representing the baud rate to use for serial communication.
    log_to_file: A string specifying the file to log serial events to, or None (the default) for no logging.

  Returns:
    A Board object which implements the firmata protocol over the specified serial port.
  """
  return Board(port, baud, log_to_file=log_to_file, start_serial=True)

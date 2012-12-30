"""Provides an API wrapper around the Firmata wire protocol.

There are two major pieces to the firmata module. When FirmataInit() is called, a thread is spun up to handle serial
port IO. Its sole function is to read bytes into the read queue and write bytes from the write queue. These queues are
then used by the main body of code to respond to API calls made by the host application.

The API presented to the host program is encapsulated in the `Board` class, instances of which are obtained by calling
the previously mentioned `FirmataInit()` function. You can create as many Board classes as you wish, but you will not
go to space today if you create more than on on the same serial port.
"""

import collections
from Queue import Queue, Empty
import threading
import time

from firmata.constants import *
from firmata.io import SerialPort


class I2CNotEnabled(Exception): pass


class I2CDevice(object):
  """Encapsulates I2C functionality."""
  def __init__(self, board):
    """Construct an I2CDevice and add a listener."""
    self.replies = Queue()
    self._shutdown = False
    self._board = board
    def I2CListener(token):
      self.replies.put(token)
      return (False, True)
    self._board.AddListener('I2C_REPLY', I2CListener)

  def I2CWrite(self, addr, reg, data):
    """Send an I2C write command.

    Args:
      addr: A byte. An I2C address. Must be less than 0x80.
      reg: A byte. The I2C register to which to write. Set to None to exclude it.
      data: A bytearray/list/string. The data to write to the I2C bus.
    """
    assert addr < 0x80
    if reg is not None:
      self._board.SendSysex(I2C_REQUEST, [addr, I2C_WRITE, reg] + data)
    else:
      self._board.SendSysex(I2C_REQUEST, [addr, I2C_WRITE] + data)

  def I2CRead(self, addr, reg, count, timeout=1):
    """Send an I2C write command.

    Args:
      addr: A byte. An I2C address. Must be less than 0x80.
      reg: A byte. The I2C register to which to write. Set to None to exclude it.
      count: A number. The number of bytes of to read from the I2C bus.
      timeout: A number. The number of seconds to wait to receieve I2C traffic before giving up.

    Returns:
      A list of tokens received from the device before the timeout.
    """
    assert addr < 0x80
    if reg is not None:
      self._board.SendSysex(SE_I2C_REQUEST, [addr, I2C_READ, reg, count])
    else:
      self._board.SendSysex(SE_I2C_REQUEST, [addr, I2C_READ, count])
    receieved = []
    start_t = time.time()
    while time.time() - timeout < start_t:
      try:
        receieved.append(self.replies.get(timeout=timeout))
      except Empty:
        continue
    return receieved

class Board(threading.Thread):
  def __init__(self, port, baud, log_to_file=None, start_serial=False):
    """Board object constructor. Should not be called directly.

    Args:
      port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
      baud: A number representing the baud rate to use for serial communication.
      log_to_file: A string specifying the file to log serial events to, or None (the default) for no logging.
      start_serial: If True, starts the serial IO thread right away. Default: False.
    """
    self.port = SerialPort(port=port, baud=baud, log_to_file=log_to_file, start_serial=start_serial)
    self.shutdown = False
    self.firmware_version = 'Unknown'
    self.firmware_name = 'Unknown'
    self.errors = []
    self.analog_channels = []
    self.pin_config = []
    self._listeners = collections.defaultdict(list)
    self._listeners_lock = threading.Lock()
    self.pin_state = collections.defaultdict(lambda: False)
    self._i2c_device = I2CDevice(self)
    super(Board, self).__init__()
    if start_serial:
      self.StartCommunications()

  def StartCommunications(self):
    """Starts all the threads needed to communicate with the physical board."""
    wait_for_serial = False
    if self.firmware_name == 'Unknown':
      wait_for_serial = threading.Condition()
      wait_for_serial.acquire()
      def FirmwareReportListener(token):
        wait_for_serial.acquire()
        wait_for_serial.notify_all()
        wait_for_serial.release()
        return (True, False)
      self.AddListener('REPORT_FIRMWARE', FirmwareReportListener)
    self.port.StartCommunications()
    self.shutdown = False
    self.start()
    if wait_for_serial:
      wait_for_serial.wait(5)
      wait_for_serial.release()

  def StopCommunications(self):
    """Stops communication with the board, and returns only after all communication has ceased."""
    self.port.StopCommunications()
    self.shutdown = True
    self.join()

  def __del__(self):
    self.port.StopCommunications()

  def AddListener(self, token_type, listener):
    """Add a callable to be called the next time a particular token_type is received.

    Args:
      token_type: A string. The type of token to listen for.
      listener: A callable taking one argument (a token), which returns a tuple (delete, abort). If delete is True,
          the callable will be deleted. If abort is True, the normal processing of this token will cease after
          callbacks are called.
    """
    self._listeners_lock.acquire()
    self._listeners[token_type].append(listener)
    self._listeners_lock.release()

  def DispatchToken(self, token):
    """Given a token, mutates Board state and calls listeners as appropriate.

    Args:
      token: A dictionary. The token to dispatch.
    Returns:
      A boolean indicating success (True) or failure (False). On failure, an error will have been appended to the error
      queue.
    """
    token_type = token['token']
    self._listeners_lock.acquire()
    my_listeners = self._listeners.get(token_type, [])
    if self._listeners[token_type]:
      del self._listeners[token_type]
    abort_regular_execution = False
    for l in my_listeners:
      delete, abort = l(token)
      if abort:
        abort_regular_execution = True
      if not delete:
        self._listeners.append(l)
    self._listeners_lock.release()
    if abort_regular_execution:
      return True
    if token_type == 'ERROR':
      self.errors.append(token['message'])
      return True
    if token_type == 'RESERVED_COMMAND':
      self.errors.append('Unable to parse a reserved command: %s' % (repr(token)))
      return False
    if token_type == 'REPORT_FIRMWARE':
      self.firmware_version = '%s.%s' % (token['major'], token['minor'])
      self.firmware_name = token['name']
      return True
    if token_type == 'ANALOG_MAPPING_RESPONSE':
      self.analog_channels = token['channels']
      return True
    if token_type == 'CAPABILITY_RESPONSE':
      self.pin_config = token['pins']
      return True
    if token_type == 'ANALOG_MESSAGE':
      self.pin_state['A%s' % token['pin']] = token['value']
      return True
    if token_type == 'DIGITAL_MESSAGE':
      for pin in xrange(1, len(token['pins'])+1):
        self.pin_state['%s:%s' % (token['port'], pin)] = token['pins'][pin-1]
      return True
    if token_type == 'PROTOCOL_VERSION':
      self.firmware_version = '%s.%s' % (token['major'], token['minor'])
      return True
    if token_type == 'PIN_STATE_RESPONSE':
      if token['mode'] == MODE_ANALOG:
        token['pin'] = 'A%s' % token['pin']
      else:
        pin_nr = token['pin']
        pin = pin_nr % 16
        port = (pin_nr - pin) / 16
        token['pin'] = '%s:%s' % (port, pin)
      self.pin_state[token['pin']] = token['data']
      return True
    self.errors.append('Unable to dispatch token: %s' % (repr(token)))
    return False

  def SendSysex(self, cmd, data=None):
    if data:
      self.port.writer.q.put([SYSEX_START, cmd] + data + [SYSEX_END])
    else:
      self.port.writer.q.put([SYSEX_START, cmd, SYSEX_END])

  def I2CConfig(self, delay):
    self.SendSysex(SE_I2C_CONFIG, [delay])
    # TODO: disable local copies of i2c pins
    return self._i2c_device

  def QueryCapabilities(self):
    wait_capabiity_response = False
    if not self.pin_config:
      wait_capabiity_response = threading.Condition()
      wait_capabiity_response.acquire()
      def CapabilityResponseListener(token):
        wait_capabiity_response.acquire()
        wait_capabiity_response.notify_all()
        wait_capabiity_response.release()
        return (True, False)
      self.AddListener('CAPABILITY_RESPONSE', CapabilityResponseListener)
    self.SendSysex(SE_CAPABILITY_QUERY)
    if wait_capabiity_response:
      wait_capabiity_response.wait(5)
      wait_capabiity_response.release()

  def QueryProtocolVersion(self):
    self.port.writer.q.put([PROTOCOL_VERSION])

  def QueryFirmwareVersionAndString(self, wait=True):
    self.SendSysex(SE_REPORT_FIRMWARE)

  def run(self):
    """Reads tokens as they come in, and dispatches them appropriately. If an error occurs, the thread terminates."""
    while not self.shutdown:
      token = None
      try:
        token = self.port.reader.q.get(timeout=0.2)
      except Empty:
        continue
      if not token or not self.DispatchToken(token):
        break


def FirmataInit(port, baud=57600, log_to_file=None):
  """Instantiate a `Board` object for a given serial port.

  Args:
    port: The serial port to use. Expressed as either a string or an integer (see pyserial docs for more info.)
    baud: A number representing the baud rate to use for serial communication.
    log_to_file: A string specifying the file to log serial events to, or None (the default) for no logging.

  Returns:
    A Board object which implements the firmata protocol over the specified serial port.
  """
  board = Board(port, baud, log_to_file=log_to_file, start_serial=True)
  board.QueryCapabilities()
  return board

__all__ = ['FirmataInit', 'Board', 'SerialPort'] + CONST_R.values()

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
from firmata.io import SerialPort


class I2CNotEnabled(Exception): pass


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
    self.i2c_enabled = False

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

  def DispatchToken(self, token):
    token_type = token['token']
    if token_type == 'ERROR':
      self.errors.append(token['message'])
      return True
    if token_type == 'RESERVED_COMMAND':
      self.errors.append('Unable to parse a reserved command: %s' % (repr(token)))
      return False
    if token_type == 'REPORT_FIRMWARE':
      self.firmware_version = '%s.%s' % (token[major], token[minor])
      self.firmware_name = token['name']
      return True
    if token_type == 'ANALOG_MAPPING_RESPONSE':
      self.analog_channels = token['channels']
      return True
    if token_type == 'CAPABILITY_RESPONSE':
      self.pin_config = token['pins']
      self.pin_state = defaultdict(False)
      return True
    if token_type == 'ANALOG_MESSAGE':
      self.pin_state['A%s' % analog_pin] = token['value']
      return True
    if token_type == 'DIGITAL_MESSAGE':
      self.pin_state[token['pin']] = token['value']
      return True
    if token_type == 'PROTOCOL_VERSION':
      self.firmware_version = '%s.%s' % (token[major], token[minor])
      return True
    if token_type == 'PIN_STATE_RESPONSE':
      if token['mode'] == MODE_ANALOG:
        token['pin'] = 'A%s' % token['pin']
      self.pin_state[token['pin']] = token['data']
      return True
    self.errors.append('Unable to dispatch token: %s' % (repr(token)))
    return False

  def SendSysex(self, cmd, data):
    self.port.writer.q.put([SE_START_SYSEX, cmd] + data + [SE_END_SYSEX))

  def I2CConfig(self, delay):
    self.SendSysex(SE_I2C_CONFIG, [delay])
    self.i2c_enabled = True

  def I2CRead(self, addr, reg, count, timeout=1):
    if not self.i2c_enabled:
      raise I2CNotEnabled
    if reg:
      self.SendSysex(SE_I2C_REQUEST, [addr, I2C_READ, reg, count])
    else:
      self.SendSysex(SE_I2C_REQUEST, [addr, I2C_READ, count])
    if self.port.reader.i2c_reply_ready.wait(timeout):
      pass # what now?
    else:
      return None

  def I2CWrite(self, addr, reg, data):
    if not self.i2c_enabled:
      raise I2CNotEnabled
    if reg:
      self.SendSysex(I2C_REQUEST, [addr, I2C_WRITE, reg] + data])
    else:
      self.SendSysex(I2C_REQUEST, [addr, I2C_WRITE] + data])

  def run(self):
    while not self.shutdown:
      token = None
      try:
        token = self.port.reader.q.get(timeout=0.2)
      except Empty:
        continue
      if not Token or not self.DispatchToken(token):
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
  return Board(port, baud, log_to_file=log_to_file, start_serial=True)

__all__ = ['FirmataInit', 'Board', 'SerialPort'] + CONST_R.values()

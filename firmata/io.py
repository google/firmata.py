from Queue import Queue, Empty
import serial
import threading
import time

from firmata.constants import *


READER_TIMEOUT = 0.2


class SerialLogger(threading.Thread):
  """Implements threadsafe logging for use with the serial port threads"""
  def __init__(self, path):
    self._file = open(path, 'w')
    self.q = Queue()
    super(SerialLogger, self).__init__()

  def run(self):
    """Consumes logging events from the queue and writes them to a file. `None` event is a signal to quit."""
    while True:
      event = self.q.get()
      if event is None:
        break
      self._file.write('%s\n' % event)
      self._file.flush()
      self.q.task_done()
    self._file.close()


class SerialWriter(threading.Thread):
  """Writes bytes from a queue to the serial port."""
  def __init__(self, port, log):
    self._port = port
    self._log = log
    self.q = Queue()
    super(SerialWriter, self).__init__()

  def run(self):
    """Writes all the bytes from `q` to the serial port, aborting if it encounters `None` on the queue"""
    self._port.flushOutput()
    while True:
      commands = self.q.get()
      if commands is None:
        return
      if type(commands) == int:
        commands = [commands]
      if type(commands) != list:
        commands = list(commands)
      self._port.write(''.join([chr(command) for command in commands]))
      for command in commands:
        if self._log:
          self._log.put('>> %s (%s)' % (hex(command), CONST_R.get(command, 'UNKNOWN')))
      self.q.task_done()


class Error(Exception): pass
class ShutdownException(Error): pass
class LexerException(Error): pass


class SerialReader(threading.Thread):
  """A serial port reader.

  Includes a lexer to convert byte sequences into Firmata protocol objects. The lexer is implemented in Rob Pike's
  handwritten style.
  """
  def __init__(self, port, log):
    self._port = port
    self._log = log
    self.q = Queue()
    self._pushback = []
    self.shutdown = False
    self.stopped = True
    self.i2c_reply_ready = threading.Event()
    super(SerialReader, self).__init__()

  def Next(self, no_high=True):
    if self.shutdown:
      return None
    if not self._pushback:
      runes = None
      while not runes:
        if self.shutdown:
          raise ShutdownException()
        if self._port.inWaiting() > 0:
          runes = self._port.read()
        else:
          time.sleep(READER_TIMEOUT)
      self._pushback = [ord(rune) for rune in reversed(runes)]
      if self._log:
        for rune in self._pushback:
          self._log.put('<< %s (%s)' % (hex(rune), CONST_R.get(rune, 'UNKNOWN')))
    rune = self._pushback.pop()
    if no_high and rune > 0x80 and rune != SYSEX_END:
      raise LexerException(self.Error('Unexpected byte with high bit set: %s. Attempting recovery.' % rune))
    return rune

  def Peek(self, no_high=True):
    rune = self.Next(no_high)
    self.Backup(rune)
    return rune

  def Backup(self, rune):
    self._pushback.append(rune)

  def Emit(self, token):
    self.q.put(token)

  def Error(self, message):
    self.Emit(dict(token='ERROR', message=message))
    return self.lexErrorRecover

  def lexErrorRecover(self):
    while self.Peek(False) > 0x80:  # Loop until next stanza (data internal to a command never has the high bit set).
      self.Next(False)
    if self.Peek(False) == SYSEX_END:  # Discard the SYSEX_END (if present) of a corrupted command.
      self.Next(False)
    return self.lexInitial

  def lexReservedCommand(self):
    data = []
    rune = self.Next()
    while rune != SYSEX_END:
      data.append(rune)
      rune = self.Next()
    self.Emit(dict(token='RESERVED_COMMAND', data=data))
    return self.lexInitial

  def lexReportFirmware(self):
    major, minor = self.Next(), self.Next()
    rune_lsb = self.Next()
    name = []
    while rune_lsb != SYSEX_END:
      rune_msb = self.Next()
      name.append(chr((rune_msb << 7) + rune_lsb))
      rune_lsb = self.Next()
    self.Emit(dict(token='REPORT_FIRMWARE', major=major, minor=minor, name=''.join(name)))
    return self.lexInitial

  def lexAnalogMappingResponse(self):
    pin_channels = []
    rune = self.Next()
    while rune != SYSEX_END:
      pin_channels.append(rune if rune != 127 else False)
      rune = self.Next()
    self.Emit(dict(token='ANALOG_MAPPING_RESPONSE', channels=pin_channels))
    return self.lexInitial

  def lexCapabilityResponse(self):
    rune = self.Next()
    pins = []
    while rune != SYSEX_END:
      mode = rune
      pin = dict()
      while mode != 127:
        pin[mode] = self.Next()
        mode = self.Next()
      pins.append(pin)
      rune = self.Next()
    self.Emit(dict(token='CAPABILITY_RESPONSE', pins=pins))
    return self.lexInitial

  def lexPinStateResponse(self):
    pin, mode = self.Next(), self.Next()
    data = []
    token = dict(token='PIN_STATE_RESPONSE', pin=pin, mode=mode, data=[])
    rune = self.Next()
    while rune != SYSEX_END:
      data.append(rune)
      rune = self.Next()
    token['data'] = sum([data[i] << (7 * i) for i in xrange(len(data))])
    self.Emit(token)
    return self.lexInitial

  def lexI2cReply(self):
    rune_lsb = self.Next()
    rune_msb = self.Next()
    addr = chr((rune_msb << 7) + rune_lsb)
    rune_lsb = self.Next()
    rune_msb = self.Next()
    reg = chr((rune_msb << 7) + rune_lsb)

    rune_lsb = self.Next()
    data = []
    while rune_lsb != SYSEX_END:
      rune_msb = self.Next()
      data.append(chr((rune_msb << 7) + rune_lsb))
      rune_lsb = self.Next()
    self.Emit(dict(token='I2C_REPLY', addr=addr, reg=reg, data=data))
    return self.lexInitial

  def lexSysex(self):
    _ = self.Next(False)
    command = self.Next(False)
    if command == SE_RESERVED_COMMAND:
      return self.lexReservedCommand
    if command == SE_ANALOG_MAPPING_RESPONSE:
      return self.lexAnalogMappingResponse
    if command == SE_CAPABILITY_RESPONSE:
      return self.lexCapabilityResponse
    if command == SE_PIN_STATE_RESPONSE:
      return self.lexPinStateResponse
    if command == SE_I2C_REPLY:
      return self.lexI2cReply
    if command == SE_REPORT_FIRMWARE:
      return self.lexReportFirmware
    return self.Error('State Sysex could not determine where to go from here given rune %s (%s)' % (hex(rune),
        CONST_R.get(rune, 'UNKNOWN')))

  def lexAnalogMessage(self):
    command, lsb, msb = self.Next(False), self.Next(), self.Next()
    self.Emit(dict(token='ANALOG_MESSAGE', pin=(command-0xE0), value=(msb << 7) + lsb))
    return self.lexInitial

  def lexDigitalMessage(self):
    command, lsb, msb = self.Next(False), self.Next(), self.Next()
    bitmask = (msb << 7) + lsb
    token_dict = dict(token='DIGITAL_MESSAGE', port=(command-0x90), pins=[])
    for pin_num in xrange(8):
      token_dict['pins'].append((bitmask % 2) == 1)
      bitmask = bitmask >> 1
    self.Emit(token_dict)
    return self.lexInitial

  def lexProtocolVersion(self):
    major, minor = self.Next(), self.Next()
    self.Emit(dict(token='PROTOCOL_VERSION', major=major, minor=minor))
    return self.lexInitial

  def lexInitial(self):
    rune = self.Peek(False)
    if ANALOG_MESSAGE_0 <= rune <= ANALOG_MESSAGE_F:
      return self.lexAnalogMessage
    if DIGITAL_MESSAGE_0 <= rune <= DIGITAL_MESSAGE_F:
      return self.lexDigitalMessage
    if rune == PROTOCOL_VERSION:
      self.Next(False)
      return self.lexProtocolVersion
    if rune == SYSEX_START:
      return self.lexSysex
    return self.Error('State Initial could not determine where to go from here given rune %s (%s)' % (hex(rune),
        CONST_R.get(rune, 'UNKNOWN')))

  def run(self):
    self._port.flushInput()
    self.stopped = False
    state = self.lexInitial
    while not self.shutdown:
      if state is None:
        break
      try:
        state = state()
      except LexerException, e:
        state = e.message
      except ShutdownException:
        break
    self.stopped = True


class SerialPort(object):
  """Represents a serial port that knows how the Firmata protocol works."""
  def __init__(self, port, baud, log_to_file=None, start_serial=True):
    """Constructs a SerialPort object.

    Args:
      port: String or integer defining a serial port. See pySerial docs for details.
      baud: An integer specifying the baud rate to use for serial communications.
      log_to_file: A string specifying the file to log serial events to, or None (the default) for no logging.
      start_serial: A boolean controlling whether the serial reader and writer threads are started as part of the
          constructor. Defaults to True.
    """
    self._port = serial.Serial(port=port, baudrate=baud)
    self._logger = None
    logger_q = None
    if log_to_file:
      self._logger = SerialLogger(log_to_file)
      self._logger.start()
      logger_q = self._logger.q
    self.reader = SerialReader(self._port, logger_q)
    self.writer = SerialWriter(self._port, logger_q)
    if start_serial:
      self.StartCommunications()

  def StartCommunications(self):
    """Starts the reader and writer threads for this serial port."""
    if not self.reader.is_alive():
      self.reader.start()
    if not self.writer.is_alive():
      self.writer.start()

  def StopCommunications(self):
    """Stops the reader and writer threads for this serial port."""
    self.reader.shutdown = True
    self.writer.q.put(None)
    self.writer.join()
    self.reader.join()
    if self._logger:
      self._logger.q.put(None)
      self._logger.join()

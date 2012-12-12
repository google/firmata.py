from Queue import Queue, Empty
import serial
import threading

from firmata.constants import *


READER_TIMEOUT = 0.2
READER_CHUNK_SIZE = 100


class SerialLogger(threading.Thread):
  """Implements threadsafe logging for use with the serial port threads"""
  def __init__(self, path):
    self._file = open(path, 'w')
    self.q = Queue()

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

  def run(self):
    while True:
      w = self.q.get()
      if w is None:
        return
      self._port.write(w)
      if self._log:
        self._log.put('>> %s (%s)' % (hex(w), CONST_R.get(w, 'UNKNOWN')))
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

  def Next(self):
    if not self._pushback:
      runes = None
      while not runes:
        if self.shutdown:
          raise ShutdownException()
        runes = self._port.read(READER_CHUNK_SIZE)
      self._pushback = [ord(rune) for rune in reversed(runes)]
    rune = self._pushpack.pop()
    if self._log:
      self._log.put('<< %s (%s)' % (hex(rune), CONST_R.get(rune, 'UNKNOWN')))
    return rune

  def Peek(self):
    rune = self.Next()
    self.Backup(rune)
    return rune

  def Backup(self, rune):
    self._pushback.append(rune)

  def Emit(self, token):
    self.q.put(token)

  def Error(self, message):
    raise LexerException(message)

  def lexReservedCommand(self):
    command = self.Next()
    data = []
    rune = self.Next()
    while rune != SYSEX_END:
      data.append(rune)
    self.Emit(dict(token='RESERVED_COMMAND', data=data))
    return self.lexInitial

  def lexReportFirmware(self):
    major, minor = self.Next(), self.Next()
    rune_lsb = self.Next()
    name = []
    while rune_lsb != SYSEX_END:
      rune_msb = self.Next()
      data.append(chr((rune_msb << 7) + rune_lsb))
      rune_lsb = self.Next()
    self.Emit(dict(token='REPORT_FIRMWARE', major=major, minor=minor, name=''.join(name)))
    return self.lexInitial

  def lexAnalogMappingResponse(self):
    pin_channels = []
    rune = self.Next()
    while rune != SYSEX_END:
      pin_channels.append(rune if rune != 127 else False)
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
    self.Error('Pin State Response is unimplemented')

  def lexI2cReply(self):
    self.Error('I2C Reply is unimplemented.')

  def lexSysex(self):
    _ = self.Next()
    command = self.Next()
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
    self.Error('State Sysex could not determine where to go from here given rune %s (%s)' % (hex(rune),
        CONST_R.get(rune, 'UNKNOWN')))

  def lexAnalogMessage(self):
    command, lsb, msb = self.Next(), self.Next(), self.Next()
    self.Emit(dict(token='ANALOG_MESSAGE', pin=(command-0xE0), value=(msb << 7) + lsb))
    return self.lexInitial

  def lexDigitalMessage(self):
    command, lsb, msb = self.Next(), self.Next(), self.Next()
    bitmask = (msb << 7) + lsb
    dict(token='DIGITAL_MESSAGE', port=(command-0x90), pins=[])
    for pin_num in xrange(14):
      token_dict['pins'][pin_num] = ((bitmask % 2) == 1)
      bitmask = bitmask >> 1
    self.Emit(token_dict)
    return self.lexInitial

  def lexProtocolVersion(self):
    _, major, minor = self.Next(), self.Next(), self.Next()
    self.Emit(dict(token='PROTOCOL_VERSION', major=major, minor=minor)
    return self.lexInitial

  def lexInitial(self):
    rune = self.Peek()
    if ANALOG_MESSAGE_0 <= rune <= ANALOG_MESSAGE_F:
      return self.lexAnalogMessage
    if DIGITAL_MESSAGE_0 <= rune <= DIGITAL_MESSAGE_F:
      return self.lexDigitalMessage
    if rune == PROTOCOL_VERSION:
      return self.lexProtocolVersion
    if rune == SYSEX_START:
      return self.lexSysex
    self.Error('State Initial could not determine where to go from here given rune %s (%s)' % (hex(rune),
        CONST_R.get(rune, 'UNKNOWN')))

  def run(self):
    self.stopped = False
    state = self.lexInitial
    while not self.shutdown:
      if state is None:
        break
      try:
        state = state()
      except LexerException, e:
        print 'ERROR: %s' % e.message
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
    self._port = serial.Serial(port=port, baudrate=baud, timeout=READER_TIMEOUT)
    self._logger = None
    if log_to_file:
      self._logger = SerialLogger(log_to_file)
      self._logger.start()
    self.reader = SerialReader(self._port, self._logger.q)
    self.writer = SerialWriter(self._port, self._logger.q)
    if start_serial:
      self.StartCommunications()

  def StartCommunications(self):
    """Starts the reader and writer threads for this serial port."""
    self.reader.start()
    self.writer.start()

  def GetToken(self, nowait=False):
    """Gets a token of input from the Firmata device.

    Args:
      nowait: A boolean. If True, GetToken returns immediately. If False, GetToken blocks until a token is available.

    Returns:
      A FirmataToken or None if nowait is True and there are no Tokens immediately available.

    Raises:
      ShutdownException if the library should shut down cleanly because the reader has stopped.
    """
    if self.reader.stopped:
      raise ShutdownException('Reader thread stopped.')
    if nowait:
      try:
        return self.reader.q.get(False)
      except Empty:
        return None
    return self.reader.q.get()

import unittest2 as unittest
import serial

import firmata
from firmata import io
from firmata.constants import *


FIRMATA_INIT = [chr(i) for i in (
  PROTOCOL_VERSION, 0x5, 0x2,  # Version 5.2
  SYSEX_START, SE_REPORT_FIRMWARE, 0x5, 0x2, 0x54, 0x0, 0x65, 0x0, 0x73, 0x0, 0x74, 0x0, SYSEX_END,  # Firmware 'Test'
)]

ARDUINO_CAPABILITY = [chr(i) for i in (
  SYSEX_START, SE_CAPABILITY_RESPONSE,
  0x7f,
  0x7f,
  0x0, 0x1, 0x1, 0x1, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x3, 0x8, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x3, 0x8, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x3, 0x8, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x3, 0x8, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x3, 0x8, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x3, 0x8, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x4, 0xe, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x2, 0xa, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x2, 0xa, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x2, 0xa, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x2, 0xa, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x2, 0xa, 0x6, 0x1, 0x7f,
  0x0, 0x1, 0x1, 0x1, 0x2, 0xa, 0x6, 0x1, 0x7f, SYSEX_END,
)]

ARDUINO_ANALOG_MAPPING = [chr(i) for i in (
  SYSEX_START, SE_ANALOG_MAPPING_RESPONSE,
  0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f, 0x7f,
  0x0, 0x01, 0x02, 0x03, 0x04, 0x05, SYSEX_END,
)]

ARDUINO_BOARD_STATE = [chr(i) for i in (
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x00, 0x01, 0x00, SYSEX_END, # pin 1, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x02, 0x01, 0x00, SYSEX_END, # pin 2, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x03, 0x01, 0x00, SYSEX_END, # pin 3, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x04, 0x01, 0x00, SYSEX_END, # pin 4, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x05, 0x01, 0x00, SYSEX_END, # pin 5, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x06, 0x01, 0x00, SYSEX_END, # pin 6, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x07, 0x01, 0x00, SYSEX_END, # pin 7, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x08, 0x01, 0x00, SYSEX_END, # pin 8, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x09, 0x01, 0x00, SYSEX_END, # pin 9, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x0a, 0x01, 0x00, SYSEX_END, # pin 10, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x0b, 0x01, 0x00, SYSEX_END, # pin 11, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x0c, 0x01, 0x00, SYSEX_END, # pin 12, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x0d, 0x01, 0x00, SYSEX_END, # pin 13, digital output, low
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x0e, 0x02, 0x00, SYSEX_END, # pin 14 (A0), analog input, 0
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x0f, 0x02, 0x00, SYSEX_END, # pin 15 (A1), analog input, 0
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x10, 0x02, 0x00, SYSEX_END, # pin 16 (A2), analog input, 0
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x11, 0x02, 0x00, SYSEX_END, # pin 17 (A3), analog input, 0
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x12, 0x02, 0x00, SYSEX_END, # pin 18 (A4), analog input, 0
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x13, 0x02, 0x00, SYSEX_END, # pin 19 (A5), analog input, 0
)]

MONDO_DATA = [chr(i) for i in (
  ANALOG_MESSAGE_0, 0x23, 0x00,  # Pin A0 set to 0x23
  DIGITAL_MESSAGE_0, 0b00000100, 0b00000000,  # Pin 2 set.
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x04, 0x01, 0x00, SYSEX_END,  # Report pin 4 mode and state
  SYSEX_START, SE_RESERVED_COMMAND, 0x20, SYSEX_END  # Hypothetical reserved command
)]

FIRMATA_UNKNOWN = [chr(i) for i in (
  SYSEX_START, SE_RESERVED_COMMAND, 0x20, SYSEX_END  # Hypothetical reserved command
)]

FIRMATA_STRING_DATA = [chr(i) for i in (
  SYSEX_START, SE_STRING_DATA, 0x48, 0x00, 0x65, 0x00, 0x6C, 0x00, 0x6C, 0x00, 0x6F, 0x00, SYSEX_END,
)]

I2C_REPLY_MESSAGE = [chr(i) for i in (
  #                         |   addr    |   reg     |   byte0   |   byte1   |
  SYSEX_START, SE_I2C_REPLY, 0x4f, 0x00, 0x00, 0x00, 0x7f, 0x01, 0x00, 0x00, SYSEX_END,
)]
I2C_REPLY_DICT = dict(token='I2C_REPLY', addr=0x4f, reg=0x00, data=[0xff, 0x00])

class MockSerial(object):
  def __init__(self, *args, **kargs):
    self.data = []
    self.output = []

  def inWaiting(self):
    return len(self.data)

  def read(self, num=1, *args, **kargs):
    if num > len(self.data):
      raise Exception('Tried to read more bytes than available.')
    ret = self.data[:num]
    del self.data[:num]
    return ret

  def write(self, bytes):
    self.output.append(bytes)

  def flushInput(self):
    pass

  def flushOutput(self):
    pass

  def close(self):
    pass

class LexerTest(unittest.TestCase):
  def setUp(self):
    super(LexerTest, self).setUp()
    self._real_serial = serial.Serial
    self._port = MockSerial()
    serial.Serial = lambda *args,**kargs: self._port

  def tearDown(self):
    super(LexerTest, self).tearDown()
    serial.Serial = self._real_serial

  def test_Basic(self):
    port = MockSerial()
    port.data = [chr(i) for i in (PROTOCOL_VERSION, 0x5, 0x2, SYSEX_START, SE_REPORT_FIRMWARE, 0x5, 0x2, 0x54, 0x0, 0x65, 0x0, 0x73, 0x0, 0x74, 0x0, SYSEX_END)]
    reader = io.SerialReader(port, None)
    state = reader.lexInitial()
    while state != reader.lexInitial:
      state = state()
    self.assertEqual(dict(token='PROTOCOL_VERSION', major=5, minor=2), reader.q.get())
    state = reader.lexInitial()
    while state != reader.lexInitial:
      state = state()
    self.assertEqual(dict(token='REPORT_FIRMWARE', major=5, minor=2, name='Test'), reader.q.get())

  def test_Mondo(self):
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:] + MONDO_DATA[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.join(timeout=1)
    board.StopCommunications()
    self.assertEqual(len(board.errors), 1)
    self.assertIn('RESERVED_COMMAND', board.errors[0])
    self.assertIn({0: 1, 1: 1, 4: 14}, board.pin_config)
    self.assertEqual(20, len(board.pin_config))
    self.assertEqual('5.2', board.firmware_version)
    self.assertEqual('Test', board.firmware_name)
    self.assertEqual(board.pin_state[13], 35)
    self.assertEqual(board.pin_state[2], True)

class FirmataTest(unittest.TestCase):
  def setUp(self):
    super(FirmataTest, self).setUp()
    self._real_serial = serial.Serial
    self._port = MockSerial()
    serial.Serial = lambda *args,**kargs: self._port

  def tearDown(self):
    super(FirmataTest, self).tearDown()
    serial.Serial = self._real_serial

  def test_QueryBoardState(self):
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:]
    self.board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    for i in xrange(20):
      self.board.QueryPinState(i)
    self.board.join(timeout=1)
    self.board.StopCommunications()
    assert self._port.output == [
       # 0xF0 (START_SYSEX), 0X6D (PIN_STATE_QUERY), pin, 0XF7 (END_SYSEX)
      '\xf0\x6d\x00\xf7', '\xf0\x6d\x01\xf7', '\xf0\x6d\x02\xf7', '\xf0\x6d\x03\xf7',
      '\xf0\x6d\x04\xf7', '\xf0\x6d\x05\xf7', '\xf0\x6d\x06\xf7', '\xf0\x6d\x07\xf7',
      '\xf0\x6d\x08\xf7', '\xf0\x6d\x09\xf7', '\xf0\x6d\x0a\xf7', '\xf0\x6d\x0b\xf7',
      '\xf0\x6d\x0c\xf7', '\xf0\x6d\x0d\xf7', '\xf0\x6d\x0e\xf7', '\xf0\x6d\x0f\xf7',
      '\xf0\x6d\x10\xf7', '\xf0\x6d\x11\xf7', '\xf0\x6d\x12\xf7', '\xf0\x6d\x13\xf7',]

  def test_FirmataInit(self):
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:] + ARDUINO_BOARD_STATE[:]
    board = firmata.Board('', 10, log_to_file='/tmp/testlog', start_serial=True)
    board.join(timeout=2)
    board.StopCommunications()
    assert board.pin_mode[2] == 1
    assert board.pin_mode[3] == 1
    assert board.pin_mode[4] == 1
    assert board.pin_mode[5] == 1
    assert board.pin_mode[6] == 1
    assert board.pin_mode[7] == 1
    assert board.pin_mode[8] == 1
    assert board.pin_mode[9] == 1
    assert board.pin_mode[10] == 1
    assert board.pin_mode[11] == 1
    assert board.pin_mode[12] == 1
    assert board.pin_mode[13] == 1
    assert board.pin_mode[14] == 2
    assert board.pin_mode[15] == 2
    assert board.pin_mode[16] == 2
    assert board.pin_mode[17] == 2
    assert board.pin_mode[18] == 2
    assert board.pin_mode[19] == 2
    for i in xrange(2,19):
      assert board.pin_state[i] == 0

  def test_basicDigitalWrite(self):
    """Test basic functionality of digitalWrite()."""
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.digitalWrite(8, 0)
    board.join(timeout=1)
    board.StopCommunications()
    assert self._port.output == ['\x91\x00\x00']

  def test_digitalWriteDoesntLeakBits(self):
    """Test that digitalWrite() doesn't let one pin's value affect another's"""
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.pin_mode[14] = MODE_OUTPUT # Lie
    board.pin_state[14] = 0xff # Same pseudo-port as pin 8
    board.digitalWrite(8, 0)
    board.join(timeout=1)
    board.StopCommunications()
    assert self._port.output == ['\x91\x40\x00']

  # This test is flaky, not sure why
  # output seen:
  #   ['\x91@\x00']
  def test_digitalWriteHasNoAnalogLeaks(self):
    """Test that analog values don't leak into digitalWrite()."""
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:] + ARDUINO_BOARD_STATE[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.pin_state[14] = 255 # Same pseudo-port as pin 8
    board.digitalWrite(8, 0)
    board.join(timeout=1)
    board.StopCommunications()
    print self._port.output
    assert self._port.output == ['\x91\x00\x00']

  def test_I2CRead(self):
    """Test simple I2C read query is properly sent and reply lexxed"""
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:] + ARDUINO_BOARD_STATE[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.I2CConfig(0)
    old_sysex = board.SendSysex
    def FakeSysex(*args, **kargs):
      self._port.data.extend(I2C_REPLY_MESSAGE[:])
      old_sysex(*args, **kargs)
    board.SendSysex = FakeSysex
    reply = board._i2c_device.I2CRead(0x4f, 0x00, 2) # read 2 bytes from register 0
    board.join(timeout=1)
    board.StopCommunications()
    #                            |    i2c config      |   | start | addr  |  reg  |   2   | end
    assert self._port.output == ['\xf0\x78\x00\x00\xf7', '\xf0\x76\x4f\x08\x00\x00\x02\x00\xf7']
    self.assertEqual(reply, I2C_REPLY_DICT['data'])

  def test_I2CWriteSend(self):
    """Test simple I2C write query is properly sent"""
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:] + ARDUINO_BOARD_STATE[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.I2CConfig(0)
    board._i2c_device.I2CWrite(0x4f, 0x00, [0x7f, 0xff]) # write 2 bytes to register 0
    board.join(timeout=1)
    board.StopCommunications()
    #                            |    i2c config      |   | start | addr  |  reg  |   2 bytes     | end
    assert self._port.output == ['\xf0\x78\x00\x00\xf7', '\xf0\x76\x4f\x00\x00\x00\x7f\x00\x7f\x01\xf7']

  def test_ListenerReuse(self):
    """Test that DispatchToken() will properly recycle listeners that request it"""
    board = firmata.Board('', 10, log_to_file=None, start_serial=False)
    def FakeListener(token):
      return (False, True) # don't delete, do abort processing
    FAKE_TOKEN = 'RESPONSE'
    board.AddListener(FAKE_TOKEN, FakeListener)
    token = {'token': FAKE_TOKEN}
    board.DispatchToken(token)
    assert board._listeners[FAKE_TOKEN] == [FakeListener]

  def test_OneTimeListener(self):
    """Test that DispatchToken() will properly delete listeners that request it"""
    board = firmata.Board('', 10, log_to_file=None, start_serial=False)
    def FakeListener(token):
      return (True, True) # do delete, do abort processing
    FAKE_TOKEN = 'RESPONSE'
    board.AddListener(FAKE_TOKEN, FakeListener)
    token = {'token': FAKE_TOKEN}
    board.DispatchToken(token)
    assert board._listeners[FAKE_TOKEN] == []

  def test_SetSamplingInterval(self):
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.SetSamplingInterval(1000)
    board.SetSamplingInterval()
    board.join(timeout=1)
    board.StopCommunications()
    assert self._port.output == ['\xf0\x7a\x68\x07\xf7', '\xf0\x7a\x13\x00\xf7']

  def test_StringData(self):
    self._port.data = FIRMATA_INIT[:] + ARDUINO_CAPABILITY[:] + ARDUINO_ANALOG_MAPPING[:] + FIRMATA_STRING_DATA[:]
    board = firmata.Board('', 10, log_to_file=None, start_serial=True)
    board.join(timeout=1)
    board.StopCommunications()
    assert board.errors == ['Hello']

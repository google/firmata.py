import unittest2 as unittest
import serial
import sys

import firmata
from firmata import io
from firmata.constants import *

MONDO_DATA = [chr(i) for i in (
  PROTOCOL_VERSION, 0x5, 0x2,  # Version 5.2
  SYSEX_START, SE_REPORT_FIRMWARE, 0x5, 0x2, 0x54, 0x0, 0x65, 0x0, 0x73, 0x0, 0x74, 0x0, SYSEX_END,  # Firmware 'Test'
  ANALOG_MESSAGE_0, 0x23, 0x00,  # Pin A00 set to 0x23
  DIGITAL_MESSAGE_1, 0x0, 0b01000000,  # Pin 1:14 set.
  SYSEX_START, SE_ANALOG_MAPPING_RESPONSE, 0x0, 0x01, 127, SYSEX_END,  # Only two analog pins, A00, A01
  SYSEX_START, SE_CAPABILITY_RESPONSE, 0x0, 0x1, 127, 0x1, 0x1, 127, SYSEX_END, # Only two pins total
  SYSEX_START, SE_PIN_STATE_RESPONSE, 0x0, 0x1, 0x1, 0x2, 0x0, SYSEX_END, # Report first pin state
  SYSEX_START, SE_RESERVED_COMMAND, 0x20, SYSEX_END # Hypothetical reserved command
)]

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

class LexerTest(unittest.TestCase):
  def setUp(self):
    super(LexerTest, self).setUp()
    self._real_serial = serial.Serial
    serial.Serial = MockSerial

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
    board = firmata.Board('', 10, log_to_file=None, start_serial=False)
    board.port._port.data = MONDO_DATA[:]
    board.StartCommunications()
    board.join()
    board.StopCommunications()
    self.assertEqual(len(board.errors), 1)
    self.assertIn('RESERVED_COMMAND', board.errors[0])
    self.assertIn({0:1}, board.pin_config)
    self.assertIn({1:1}, board.pin_config)
    self.assertEqual(2, len(board.pin_config))
    self.assertEqual([0,1,False], board.analog_channels)
    self.assertEqual(257, board.pin_state[0])
    self.assertEqual('5.2', board.firmware_version)
    self.assertEqual('Test', board.firmware_name)

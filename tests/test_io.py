import unittest2 as unittest
import serial

from firmata import io
from firmata.constants import *

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

  def test_ProtocolVersion(self):
    port = MockSerial()
    port.data = [chr(i) for i in (PROTOCOL_VERSION, 0x5, 0x2)]
    reader = io.SerialReader(port, None)
    state = reader.lexInitial()
    while state != reader.lexInitial:
      state = state()
    self.assertEqual(dict(token='PROTOCOL_VERSION', major=5, minor=2), reader.q.get())

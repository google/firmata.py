import unittest2 as unittest
import serial

import firmata
from firmata.utils import *


class UtilsTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_encodeSequence(self):
    self.assertEqual(encodeSequence([255, 0, 36]), [127, 1, 0, 0, 36, 0])

  def test_decodeSequence(self):
    self.assertEqual(decodeSequence([127, 1, 0, 0, 36, 0]), [255, 0, 36])

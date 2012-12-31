"""
utils.py

Utilities that are useful when working with Firmata.
"""

def encodeSequence(data):
  """ Encode a sequence of 14 bit values as pairs of 7 bit values."""
  ret = []
  for i in data:
    ret.append(i & 0x7F)
    ret.append(i >> 7)
  return ret

def decodeSequence(data):
  """ Decode a series of pairs of 7 bit values into 14 bit values."""
  ret = []
  for i in range(0, len(data), 2):
    ret.append(data[i] + (data[i+1] << 7))
  return ret

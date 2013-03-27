# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

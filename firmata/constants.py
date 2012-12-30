"""Constants used by the Firmata wire protocol."""


# Pin mode constants
MODE_INPUT = 0
MODE_OUTPUT = 1
MODE_ANALOG = 2
MODE_PWM = 3
MODE_SERVO = 4
MODE_SHIFT = 5
MODE_I2C = 6
MODE_MAX = 6

# I2C command constants
I2C_READ = 0b00001000,
I2C_WRITE = 0b00000000


CONST = dict(
  ANALOG_MESSAGE = 0xE0,
  ANALOG_MESSAGE_0 = 0xE0,
  ANALOG_MESSAGE_1 = 0xE1,
  ANALOG_MESSAGE_2 = 0xE2,
  ANALOG_MESSAGE_3 = 0xE3,
  ANALOG_MESSAGE_4 = 0xE4,
  ANALOG_MESSAGE_5 = 0xE5,
  ANALOG_MESSAGE_6 = 0xE6,
  ANALOG_MESSAGE_7 = 0xE7,
  ANALOG_MESSAGE_8 = 0xE8,
  ANALOG_MESSAGE_9 = 0xE9,
  ANALOG_MESSAGE_A = 0xEA,
  ANALOG_MESSAGE_B = 0xEB,
  ANALOG_MESSAGE_C = 0xEC,
  ANALOG_MESSAGE_D = 0xED,
  ANALOG_MESSAGE_E = 0xEE,
  ANALOG_MESSAGE_F = 0xEF,
  DIGITAL_MESSAGE = 0x90,
  DIGITAL_MESSAGE_0 = 0x90,
  DIGITAL_MESSAGE_1 = 0x91,
  DIGITAL_MESSAGE_2 = 0x92,
  DIGITAL_MESSAGE_3 = 0x93,
  DIGITAL_MESSAGE_4 = 0x94,
  DIGITAL_MESSAGE_5 = 0x95,
  DIGITAL_MESSAGE_6 = 0x96,
  DIGITAL_MESSAGE_7 = 0x97,
  DIGITAL_MESSAGE_8 = 0x98,
  DIGITAL_MESSAGE_9 = 0x99,
  DIGITAL_MESSAGE_A = 0x9A,
  DIGITAL_MESSAGE_B = 0x9B,
  DIGITAL_MESSAGE_C = 0x9C,
  DIGITAL_MESSAGE_D = 0x9D,
  DIGITAL_MESSAGE_E = 0x9E,
  DIGITAL_MESSAGE_F = 0x9F,
  REPORT_ANALOG = 0xC0,
  REPORT_ANALOG_0 = 0xC0,
  REPORT_ANALOG_1 = 0xC1,
  REPORT_ANALOG_2 = 0xC2,
  REPORT_ANALOG_3 = 0xC3,
  REPORT_ANALOG_4 = 0xC4,
  REPORT_ANALOG_5 = 0xC5,
  REPORT_ANALOG_6 = 0xC6,
  REPORT_ANALOG_7 = 0xC7,
  REPORT_ANALOG_8 = 0xC8,
  REPORT_ANALOG_9 = 0xC9,
  REPORT_ANALOG_A = 0xCA,
  REPORT_ANALOG_B = 0xCB,
  REPORT_ANALOG_C = 0xCC,
  REPORT_ANALOG_D = 0xCD,
  REPORT_ANALOG_E = 0xCE,
  REPORT_ANALOG_F = 0xCF,
  REPORT_DIGITAL = 0xD0,
  REPORT_DIGITAL_0 = 0xD0,
  REPORT_DIGITAL_1 = 0xD1,
  REPORT_DIGITAL_2 = 0xD2,
  REPORT_DIGITAL_3 = 0xD3,
  REPORT_DIGITAL_4 = 0xD4,
  REPORT_DIGITAL_5 = 0xD5,
  REPORT_DIGITAL_6 = 0xD6,
  REPORT_DIGITAL_7 = 0xD7,
  REPORT_DIGITAL_8 = 0xD8,
  REPORT_DIGITAL_9 = 0xD9,
  REPORT_DIGITAL_A = 0xDA,
  REPORT_DIGITAL_B = 0xDB,
  REPORT_DIGITAL_C = 0xDC,
  REPORT_DIGITAL_D = 0xDD,
  REPORT_DIGITAL_E = 0xDE,
  REPORT_DIGITAL_F = 0xDF,
  SYSEX_START = 0xF0,
  SET_PIN_MODE = 0xF4,
  SYSEX_END = 0xF7,
  PROTOCOL_VERSION = 0xF9,
  SYSTEM_RESET = 0xFF,

  # SYSEX Commands
  SE_RESERVED_COMMAND = 0x00, # 2nd SysEx data byte is a chip-specific command (AVR, PIC, TI, etc).
  SE_ANALOG_MAPPING_QUERY = 0x69, # ask for mapping of analog to pin numbers
  SE_ANALOG_MAPPING_RESPONSE = 0x6A, # reply with mapping info
  SE_CAPABILITY_QUERY = 0x6B, # ask for supported modes and resolution of all pins
  SE_CAPABILITY_RESPONSE = 0x6C, # reply with supported modes and resolution
  SE_PIN_STATE_QUERY = 0x6D, # ask for a pin's current mode and value
  SE_PIN_STATE_RESPONSE = 0x6E, # reply with a pin's current mode and value
  SE_EXTENDED_ANALOG = 0x6F, # analog write (PWM, Servo, etc) to any pin
  SE_SERVO_CONFIG = 0x70, # set max angle, minPulse, maxPulse, freq
  SE_STRING_DATA = 0x71, # a string message with 14-bits per char
#  SE_SHIFT_DATA = 0x75, # shiftOut config/data message (34 bits)
  SE_I2C_REQUEST = 0x76, # I2C request messages from a host to an I/O board
  SE_I2C_REPLY = 0x77, # I2C reply messages from an I/O board to a host
  SE_I2C_CONFIG = 0x78, # Configure special I2C settings such as power pins and delay times
  SE_REPORT_FIRMWARE = 0x79, # report name and version of the firmware
  SE_SAMPLING_INTERVAL = 0x7A, # sampling interval
#  SE_SYSEX_NON_REALTIME = 0x7E, # MIDI Reserved for non-realtime messages
#  SE_SYSEX_REALTIME = 0x7F, # MIDI Reserved for realtime messages
)


globals().update(CONST)


CONST_R = {v:k for (k,v) in CONST.items()}

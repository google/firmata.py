"""Constants used by the Firmata wire protocol."""

CONST = dict(
  ANALOG_MESSAGE = 0xE0,
  DIGITAL_MESSAGE = 0x90,
  REPORT_ANALOG = 0xC0,
  REPORT_DIGITAL = 0xD0,
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
  SE_SHIFT_DATA = 0x75, # shiftOut config/data message (34 bits)
  SE_I2C_REQUEST = 0x76, # I2C request messages from a host to an I/O board
  SE_I2C_REPLY = 0x77, # I2C reply messages from an I/O board to a host
  SE_I2C_CONFIG = 0x78, # Configure special I2C settings such as power pins and delay times
  SE_REPORT_FIRMWARE = 0x79, # report name and version of the firmware
  SE_SAMPLING_INTERVAL = 0x7A, # sampling interval
  SE_SYSEX_NON_REALTIME = 0x7E, # MIDI Reserved for non-realtime messages
  SE_SYSEX_REALTIME = 0x7F, # MIDI Reserved for realtime messages
)

globals().update(CONST)

CONST_R = {v:k for (k,v) in CONST.items()}

"""Central mapping for DartConnect button identifiers."""

# Login and session controls
LOGIN_EMAIL = "pl-email-login"
LOGIN_PASSWORD = "pl-password"
LOGIN_SUBMIT = "pl-ok"
CONFIRM_WIN = "confirm-ok"
WINNING_DART_NUMBER = "swdm-dart-{index}"

# Numeric keypad
X01_DIGITS = {
    "0": "kp-p-00",
    "1": "kp-p-01",
    "2": "kp-p-02",
    "3": "kp-p-03",
    "4": "kp-p-04",
    "5": "kp-p-05",
    "6": "kp-p-06",
    "7": "kp-p-07",
    "8": "kp-p-08",
    "9": "kp-p-09",
}
X01_PLUS = "kp-p-plus"

# Cricket buttons keyed by dart code
CRICKET_CODES = {
    "S20": "sb-c-b1S",
    "D20": "sb-c-b1D",
    "T20": "sb-c-b1T",
    "S19": "sb-c-b2S",
    "D19": "sb-c-b2D",
    "T19": "sb-c-b2T",
    "S18": "sb-c-b3S",
    "D18": "sb-c-b3D",
    "T18": "sb-c-b3T",
    "S17": "sb-c-b4S",
    "D17": "sb-c-b4D",
    "T17": "sb-c-b4T",
    "S16": "sb-c-b5S",
    "D16": "sb-c-b5D",
    "T16": "sb-c-b5T",
    "S15": "sb-c-b6S",
    "D15": "sb-c-b6D",
    "T15": "sb-c-b6T",
    "25": "sb-c-b7S",
    "Bull": "sb-c-b7D",
}

ENTER_SCORE = "mb-ig-funcr"

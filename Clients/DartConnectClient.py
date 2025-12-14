import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .DartConnect_button_ids import (
    CONFIRM_WIN,
    CRICKET_CODES,
    ENTER_SCORE,
    LOGIN_EMAIL,
    LOGIN_PASSWORD,
    LOGIN_SUBMIT,
    WINNING_DART_NUMBER,
    X01_DIGITS,
    X01_PLUS,
)

class DartConnectClient:
    def __init__(self) -> None:
        self.url_DartConnect = 'https://app.dartconnect.com/'
        self.last_turn_state = None
        self.last_dart = None  # tuple of (code, x, y) or None

        dc_options = Options()
        dc_options.add_argument("--start-maximized")
        self.dc_driver = webdriver.Chrome(options=dc_options)
        self.dc_driver.get(self.url_DartConnect)

        # Attempt automatic login from environment variables
        username = os.getenv("DARTCONNECT_USERNAME", "REPLACE_ME")
        password = os.getenv("DARTCONNECT_PASSWORD", "")
        WebDriverWait(self.dc_driver, 5).until(
            EC.visibility_of_element_located((By.ID, LOGIN_EMAIL))
        )
        self.logInDartConnect(username=username, password=password)

    def logInDartConnect(self, username: str = '', password: str = ''):
        # if username == '' or password == '':
        #     print('Please sign into DartConnect...')
        #     return

        try:
            logInBox = self.dc_driver.find_element(By.ID, LOGIN_EMAIL)
            logInBox.send_keys(username)

            passwordBox = self.dc_driver.find_element(By.ID, LOGIN_PASSWORD)
            passwordBox.send_keys(password)

            buttonOK = self.dc_driver.find_element(By.ID, LOGIN_SUBMIT)
            buttonOK.click()
        except Exception:
            print('Automatic Log-in was unsuccessful. Please log-in manually.')
            return

    def checkEndGame(self, num_throws: int = 0):
        """Handle end-of-game prompt and return True if game is over."""
        try:
            confirm_button = self.dc_driver.find_element(By.ID, CONFIRM_WIN)
            if confirm_button:
                try:
                    confirm_button.click()
                except Exception:
                    return False
                if 1 <= num_throws <= 3:
                    try:
                        self.dc_driver.find_element(By.ID, WINNING_DART_NUMBER.format(index=num_throws)).click()
                    except Exception:
                        return False
        except Exception:
            pass

        # try:
        #     controlButton = self.dc_driver.find_element(By.ID, 'mb-ig-control')
        #     return controlButton.text == ''
        # except Exception:
        #     return False
        return False

    def calcScore_x01(self, currentTurn=''):
        score = 0
        for throw in currentTurn:
            char = throw[0]
            if char == 'S':
                score = score + 1 * int(throw[1:None])
            elif char == 'D':
                score = score + 2 * int(throw[1:None])
            elif char == 'T':
                score = score + 3 * int(throw[1:None])
            elif throw == '25':
                score = score + 25
            elif throw == 'Bull':
                score = score + 50
            else:
                score = score + 0

        return score

    def enterScore_x01(self, score=''):
        if score == 0:
            return

        for digit in str(score):
            if digit == '0':
                time.sleep(0.2) # TODO: Do we still need this delay if we already check for 0 score?
            button_id = X01_DIGITS.get(digit)
            if button_id:
                self.dc_driver.find_element(By.ID, button_id).click()

        self.dc_driver.find_element(By.ID, X01_PLUS).click()

    def enterScore_cricket(self, currentTurn=''):
        for turn in currentTurn:
            button_id = CRICKET_CODES.get(turn)
            if button_id:
                self.dc_driver.find_element(By.ID, button_id).click()

    def endTurn(self):
        self.dc_driver.find_element(By.ID, ENTER_SCORE).click()

    def handle_turn_state(self, turn_state: str, game_type: str):
        """Store the latest turn_state coming from Autodarts and enter score when appropriate."""
        if turn_state is None:
            return

        self.last_turn_state = turn_state
        dart_code = None

        if turn_state.startswith("dart:"):
            # Format: dart:CODE x y (x/y may be 'None')
            _, payload = turn_state.split(":", 1)
            parts = payload.split()
            if len(parts) == 3:
                dart_code, x_str, y_str = parts
                try:
                    x_val = float(x_str) if x_str != "None" else None
                    y_val = float(y_str) if y_str != "None" else None
                except ValueError:
                    x_val = None
                    y_val = None
                self.last_dart = (dart_code, x_val, y_val)
        else:
            self.last_dart = None

        # Only enter a score if we have a valid dart code
        # TODO: Maybe add ability to score all darts at once after turn completes
        if dart_code:
            match game_type:
                case 'Cricket':
                    self.enterScore_cricket([dart_code, '-', '-'])
                case _:
                    score = self.calcScore_x01([dart_code, '-', '-'])
                    self.enterScore_x01(score)

    def quit(self):
        self.dc_driver.quit()

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os

# TODO: Maybe add a file that holds and maps all the special button IDs to their meaning. Then reference the meaning, and if ID changes, just change in the refernce file.
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
        # TODO: Improve method to wait for page load before attempting login
        time.sleep(2)  # Wait for page to load
        self.logInDartConnect(username=username, password=password)

    def logInDartConnect(self, username: str = '', password: str = ''):
        # if username == '' or password == '':
        #     print('Please sign into DartConnect...')
        #     return

        try:
            logInBox = self.dc_driver.find_element(By.ID, 'pl-email-login')
            logInBox.send_keys(username)

            passwordBox = self.dc_driver.find_element(By.ID, 'pl-password')
            passwordBox.send_keys(password)

            buttonOK = self.dc_driver.find_element(By.ID, 'pl-ok')
            buttonOK.click()
        except Exception:
            print('Automatic Log-in was unsuccessful. Please log-in manually.')
            return

    def checkEndGame(self, num_throws: int = 0):
        """Handle end-of-game prompt and return True if game is over."""
        try:
            confirm_button = self.dc_driver.find_element(By.ID, 'confirm-ok')
            if confirm_button:
                try:
                    confirm_button.click()
                except Exception:
                    pass
                if 1 <= num_throws <= 3:
                    try:
                        self.dc_driver.find_element(By.ID, f'swdm-dart-{num_throws}').click()
                    except Exception:
                        pass
                return True
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
                time.sleep(0.1) # TODO: Do we still need this delay if we already check for 0 score?
                self.dc_driver.find_element(By.ID, 'kp-p-00').click()
            elif digit == '1':
                self.dc_driver.find_element(By.ID, 'kp-p-01').click()
            elif digit == '2':
                self.dc_driver.find_element(By.ID, 'kp-p-02').click()
            elif digit == '3':
                self.dc_driver.find_element(By.ID, 'kp-p-03').click()
            elif digit == '4':
                self.dc_driver.find_element(By.ID, 'kp-p-04').click()
            elif digit == '5':
                self.dc_driver.find_element(By.ID, 'kp-p-05').click()
            elif digit == '6':
                self.dc_driver.find_element(By.ID, 'kp-p-06').click()
            elif digit == '7':
                self.dc_driver.find_element(By.ID, 'kp-p-07').click()
            elif digit == '8':
                self.dc_driver.find_element(By.ID, 'kp-p-08').click()
            elif digit == '9':
                self.dc_driver.find_element(By.ID, 'kp-p-09').click()

        self.dc_driver.find_element(By.ID, 'kp-p-plus').click()

    def enterScore_cricket(self, currentTurn=''):
        for turn in currentTurn:
            if turn == 'S20':
                self.dc_driver.find_element(By.ID, 'sb-c-b1S').click()
            elif turn == 'D20':
                self.dc_driver.find_element(By.ID, 'sb-c-b1D').click()
            elif turn == 'T20':
                self.dc_driver.find_element(By.ID, 'sb-c-b1T').click()
            elif turn == 'S19':
                self.dc_driver.find_element(By.ID, 'sb-c-b2S').click()
            elif turn == 'D19':
                self.dc_driver.find_element(By.ID, 'sb-c-b2D').click()
            elif turn == 'T19':
                self.dc_driver.find_element(By.ID, 'sb-c-b2T').click()
            elif turn == 'S18':
                self.dc_driver.find_element(By.ID, 'sb-c-b3S').click()
            elif turn == 'D18':
                self.dc_driver.find_element(By.ID, 'sb-c-b3D').click()
            elif turn == 'T18':
                self.dc_driver.find_element(By.ID, 'sb-c-b3T').click()
            elif turn == 'S17':
                self.dc_driver.find_element(By.ID, 'sb-c-b4S').click()
            elif turn == 'D17':
                self.dc_driver.find_element(By.ID, 'sb-c-b4D').click()
            elif turn == 'T17':
                self.dc_driver.find_element(By.ID, 'sb-c-b4T').click()
            elif turn == 'S16':
                self.dc_driver.find_element(By.ID, 'sb-c-b5S').click()
            elif turn == 'D16':
                self.dc_driver.find_element(By.ID, 'sb-c-b5D').click()
            elif turn == 'T16':
                self.dc_driver.find_element(By.ID, 'sb-c-b5T').click()
            elif turn == 'S15':
                self.dc_driver.find_element(By.ID, 'sb-c-b6S').click()
            elif turn == 'D15':
                self.dc_driver.find_element(By.ID, 'sb-c-b6D').click()
            elif turn == 'T15':
                self.dc_driver.find_element(By.ID, 'sb-c-b6T').click()
            elif turn == '25':
                self.dc_driver.find_element(By.ID, 'sb-c-b7S').click()
            elif turn == 'Bull':
                self.dc_driver.find_element(By.ID, 'sb-c-b7D').click()

    def endTurn(self):
        self.dc_driver.find_element(By.ID, 'mb-ig-funcr').click()

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

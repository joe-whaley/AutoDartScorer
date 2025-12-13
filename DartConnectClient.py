from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time


class DartConnectClient:
    def __init__(self) -> None:
        self.url_DartConnect = 'https://app.dartconnect.com/'

        dc_options = Options()
        dc_options.add_argument("--start-maximized")
        self.dc_driver = webdriver.Chrome(options=dc_options)
        self.dc_driver.get(self.url_DartConnect)

    def DC_logInDartConnect(self, username: str = '', password: str = ''):
        # NOTE: This is currently unused
        if username == '' or password == '':
            print('Please sign into DartConnect...')
            return

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

    def DC_checkEndGame(self):
        controlButton = self.dc_driver.find_element(By.ID, 'mb-ig-control')
        return controlButton.text == ''

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

    def DC_enterScore_x01(self, score=''):
        if score == 0:
            return

        for digit in str(score):
            if digit == '0':
                time.sleep(0.1)
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

    def DC_enterScore_cricket(self, currentTurn=''):
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

    def DC_endTurn(self):
        self.dc_driver.find_element(By.ID, 'mb-ig-funcr').click()

    def quit(self):
        self.dc_driver.quit()

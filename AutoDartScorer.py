# Auto Dart Scorer
# 1. Enter/Save your unique url for your AutoDarts Board Manager's webpage
# 2. Start up your AutoDarts application so it's ready to begin scoring/playing
# 3. Run this script from cmd/powershell window: "python ./AutoDartScorer.py"
# 4. Log into Dart Connect from the window that pops up
# 5. Start a game of 501/301/Cricket in DartConnect
# 6. Select the same game from the cmd/powershell window
# 7. Start playing!

# NOTE: Darts are scored individually as you throw.
# NOTE: Your turn is NOT scored until you RETRIEVE YOUR DARTS.
# NOTE: If you wish to make a change/correction to the score in DartConnect,
#       make sure you do so BEFORE retrieving your darts.

# Import Libraries
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

# NOTE: Requires selenium and a Google Chrome Driver
#       See: https://selenium-python.readthedocs.io/
#       See: https://youtu.be/Xjv1sY630Uc?si=Y6WswM9gbZfpBiBH

class AutoScorer():
    def __init__(self) -> None:
        # Constants
        self.url_DartConnect = 'https://app.dartconnect.com/'
        self.boardManager_AutoDarts = 'TODO-ADD-YOUR-BOARD-MANAGERS-URL-HERE'
        # NOTE: boardManager credentials are unique to you

        # Set Up Driver
        path = 'C:\Program Files (x86)\chromedriver.exe'
        self.driver = webdriver.Chrome(path)

        # Open Dart Connect
        self.driver.get(self.url_DartConnect)
        self.dartConnectWindow = self.driver.current_window_handle

        # Open Autodarts Board Manager
        self.driver.switch_to.new_window()
        self.autodartsWindow = self.driver.current_window_handle
        self.driver.get(self.boardManager_AutoDarts)

    def DC_logInDartConnect(self, username = '', password = ''):
        # NOTE: This is currently unused
        self.driver.switch_to.window(self.dartConnectWindow)

        if username == '' | password == '':
            print('Please sign into DartConnect...')
            return
        
        try:
            logInBox = self.driver.find_element(By.ID, 'pl-email-login')
            logInBox.send_keys(username)

            passwordBox = self.driver.find_element(By.ID, 'pl-password')
            passwordBox.send_keys(password)

            buttonOK = self.driver.find_element(By.ID, 'pl-ok')
            buttonOK.click()
        except:
            print('Automatic Log-in was unsuccessful. Please log-in manually.')
            return

    def enterGlobalLobby(self):
        # NOTE: Unused
        print('TODO?')

    def DC_checkEndGame(self):
        # Check if game is over
        # NOTE: A little bit of a hack, this is going to cause an error if a game ended (expected behavior)
        self.driver.switch_to.window(self.dartConnectWindow)
        controlButton = self.driver.find_element(By.ID, 'mb-ig-control')
        return controlButton.text == '' # If this is true, it is my turn
    
    def calcScore_x01(self, currentTurn = ''):
        # NOTE: This is written to support entering currentTurn as 1 Dart or multiple Darts at a time
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
                score = score + 0 # char is either 'M' or '-'

        return score
    
    def DC_enterScore_x01(self, score = ''):
        self.driver.switch_to.window(self.dartConnectWindow)
        if score == 0:
            return # Short circuit return if miss/no-score
        
        for digit in str(score):
            if digit == '0':
                time.sleep(0.1) # Annoying, but need to wait for the 0 to pop-up in the window first
                self.driver.find_element(By.ID, 'kp-p-00').click()
            elif digit == '1':
                self.driver.find_element(By.ID, 'kp-p-01').click()
            elif digit == '2':
                self.driver.find_element(By.ID, 'kp-p-02').click()
            elif digit == '3':
                self.driver.find_element(By.ID, 'kp-p-03').click()
            elif digit == '4':
                self.driver.find_element(By.ID, 'kp-p-04').click()
            elif digit == '5':
                self.driver.find_element(By.ID, 'kp-p-05').click()
            elif digit == '6':
                self.driver.find_element(By.ID, 'kp-p-06').click()
            elif digit == '7':
                self.driver.find_element(By.ID, 'kp-p-07').click()
            elif digit == '8':
                self.driver.find_element(By.ID, 'kp-p-08').click()
            elif digit == '9':
                self.driver.find_element(By.ID, 'kp-p-09').click()

        self.driver.find_element(By.ID, 'kp-p-plus').click()

    def DC_enterScore_cricket(self, currentTurn = ''):
        # NOTE: This is written to support entering currentTurn as 1 Dart or multiple Darts at a time
        self.driver.switch_to.window(self.dartConnectWindow)

        for turn in currentTurn:
            if turn == 'S20':
                self.driver.find_element(By.ID, 'sb-c-b1S').click()
            elif turn == 'D20':
                self.driver.find_element(By.ID, 'sb-c-b1D').click()
            elif turn == 'T20':
                self.driver.find_element(By.ID, 'sb-c-b1T').click()
            elif turn == 'S19':
                self.driver.find_element(By.ID, 'sb-c-b2S').click()
            elif turn == 'D19':
                self.driver.find_element(By.ID, 'sb-c-b2D').click()
            elif turn == 'T19':
                self.driver.find_element(By.ID, 'sb-c-b2T').click()
            elif turn == 'S18':
                self.driver.find_element(By.ID, 'sb-c-b3S').click()
            elif turn == 'D18':
                self.driver.find_element(By.ID, 'sb-c-b3D').click()
            elif turn == 'T18':
                self.driver.find_element(By.ID, 'sb-c-b3T').click()
            elif turn == 'S17':
                self.driver.find_element(By.ID, 'sb-c-b4S').click()
            elif turn == 'D17':
                self.driver.find_element(By.ID, 'sb-c-b4D').click()
            elif turn == 'T17':
                self.driver.find_element(By.ID, 'sb-c-b4T').click()
            elif turn == 'S16':
                self.driver.find_element(By.ID, 'sb-c-b5S').click()
            elif turn == 'D16':
                self.driver.find_element(By.ID, 'sb-c-b5D').click()
            elif turn == 'T16':
                self.driver.find_element(By.ID, 'sb-c-b5T').click()
            elif turn == 'S15':
                self.driver.find_element(By.ID, 'sb-c-b6S').click()
            elif turn == 'D15':
                self.driver.find_element(By.ID, 'sb-c-b6D').click()
            elif turn == 'T15':
                self.driver.find_element(By.ID, 'sb-c-b6T').click()
            elif turn == '25':
                self.driver.find_element(By.ID, 'sb-c-b7S').click()
            elif turn == 'Bull':
                self.driver.find_element(By.ID, 'sb-c-b7D').click()
    
    def AD_checkThrow(self):
        # Return value of each dart
        self.driver.switch_to.window(self.autodartsWindow)
        fullData = self.driver.find_element(By.CLASS_NAME, 'css-1kgqfvv').text.split('\n')
        return fullData[5:None]

    def AD_checkTurnEnd(self):
        # Monitor 'Takeout in progress' to end turn
        self.driver.switch_to.window(self.autodartsWindow)
        fullData = self.driver.find_element(By.CLASS_NAME, 'css-1kgqfvv').text.split('\n')
        return fullData[3] == 'Takeout in progress'
    
    def DC_endTurn(self):
        # Enter score for turn, if this fails, it's becuase the game is over
        self.driver.switch_to.window(self.dartConnectWindow)
        self.driver.find_element(By.ID, 'mb-ig-funcr').click()

    def AD_manualReset(self):
        # Reset the Autodarts monitor if it gets stuck in 'Takeout in progress'
        self.driver.switch_to.window(self.autodartsWindow)
        self.driver.find_elements(By.CLASS_NAME, 'chakra-button.css-k9nurg')[1].click()

    def checkNextDart(self, currentThrow = '', prevThrow = ''):
        # Only return the most recently thrown dart
        i = 0
        for turn in currentThrow:
            if turn != prevThrow[i]:
                return turn
            i = i + 1

    def AD_isMyTurn(self):
        # Checks if the player has started throwing their darts
        self.driver.switch_to.window(self.autodartsWindow)
        curThrow = self.AD_checkThrow()
        return curThrow != ['-', '-', '-']

    def DC_playGame(self, gameType = ''):
        print('Now Playing ' + gameType + '...')
        print('GAME ON!')
        isMyTurn = False
        doubledIn = False
        while True:
            try:
                time.sleep(1) # Check once a second to avoid spamming webpages
                if self.AD_checkTurnEnd():
                    # Then manually restart autodarts
                    self.AD_manualReset()
                prevThrow = ['-', '-', '-']
                isMyTurn = self.AD_isMyTurn()
                while isMyTurn:
                    time.sleep(1) # Check once a second to avoid spamming webpages
                    curThrow = self.AD_checkThrow()
                    curDart = self.checkNextDart(curThrow, prevThrow)

                    if prevThrow != curThrow:
                        match gameType:
                            case '501':
                                score = self.calcScore_x01([curDart, '-', '-'])
                                self.DC_enterScore_x01(score)
                            case '301':
                                if doubledIn == False:
                                    doubledIn = (curDart[0] == 'D') | (curDart == 'Bull')

                                if doubledIn:
                                    score = self.calcScore_x01([curDart, '-', '-'])
                                    self.DC_enterScore_x01(score)
                            case 'Cricket':
                                self.DC_enterScore_cricket([curDart, '-', '-'])

                    if self.AD_checkTurnEnd():
                        self.DC_endTurn()
                        self.DC_checkEndGame()
                        isMyTurn = False

                    prevThrow = curThrow
            except:
                # Wrap the whole thing in try statement to detect failure, likely because the game ended
                return



if __name__ == '__main__':
    app = AutoScorer()
    print('Welcome to AutoScorer!')
    print('Your DartConnect/AutoDarts Link!')
    while True:
        gameType = input('Enter 501, 301, Cricket, or Quit: ')
        match gameType:
            case '501' | '301' | 'Cricket':
                app.DC_playGame(gameType)
                print('GAME OVER')
            case 'Quit':
                print('Thank you! Goodbye!')
                time.sleep(2)
                app.driver.quit()
                quit()
            case _:
                print('Invalid Input, Please Try Again!')
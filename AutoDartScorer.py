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
import os
import time

from DartConnectClient import DartConnectClient
from AutoDartsClient import AutodartsAPIClient, AutodartsConfig

# NOTE: Requires selenium and a Google Chrome Driver
#       See: https://selenium-python.readthedocs.io/
#       See: https://youtu.be/Xjv1sY630Uc?si=Y6WswM9gbZfpBiBH

class AutoScorer():
    def __init__(self) -> None:
        # Constants
        self.boardManager_AutoDarts = os.getenv('AUTODARTS_BASE_URL', 'http://localhost:3180')
        self.autodarts_api_key = os.getenv('AUTODARTS_API_KEY', 'REPLACE_ME')
        self.autodarts_board_id = os.getenv('AUTODARTS_BOARD_ID', 'REPLACE_ME')

        # Open Dart Connect (visible window)
        self.dc_client = DartConnectClient()

        # Autodarts via WebSocket client
        cfg = AutodartsConfig(
            base_url=self.boardManager_AutoDarts,
            api_key=self.autodarts_api_key,
            board_id=self.autodarts_board_id,
        )
        self.autodarts_client = AutodartsAPIClient(cfg)
        self.autodarts_client.on_event = self.handle_autodarts_event
        self.autodarts_client.start_event_stream()

        # Track latest autodarts state
        self.current_throws = ['-', '-', '-']
        self.takeout_in_progress = False
    
    def handle_autodarts_event(self, event: dict):
        # Update throws / takeout flags from Autodarts WebSocket events
        if event.get('type') != 'state':
            return

        data = event.get('data', {})
        event_name = data.get('event', '')

        if 'throws' in data:
            self.current_throws = data.get('throws', self.current_throws)

        if event_name == 'Takeout in progress':
            self.takeout_in_progress = True
        elif event_name == 'Throw detected':
            self.takeout_in_progress = False

    def AD_checkThrow(self):
        # Return value of each dart from latest Autodarts event
        return self.current_throws

    def AD_checkTurnEnd(self):
        # Detect turn end based on takeout flag
        return self.takeout_in_progress

    def checkNextDart(self, currentThrow = '', prevThrow = ''):
        # Only return the most recently thrown dart
        i = 0
        for turn in currentThrow:
            if turn != prevThrow[i]:
                return turn
            i = i + 1

    def AD_isMyTurn(self):
        # Checks if the player has started throwing their darts
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
                prevThrow = ['-', '-', '-']
                isMyTurn = self.AD_isMyTurn()
                while isMyTurn:
                    time.sleep(1) # Check once a second to avoid spamming webpages
                    curThrow = self.AD_checkThrow()
                    curDart = self.checkNextDart(curThrow, prevThrow)

                    if prevThrow != curThrow:
                        match gameType:
                            case '501':
                                score = self.dc_client.calcScore_x01([curDart, '-', '-'])
                                self.dc_client.DC_enterScore_x01(score)
                            case '301':
                                if doubledIn == False:
                                    doubledIn = (curDart[0] == 'D') or (curDart == 'Bull')

                                if doubledIn:
                                    score = self.dc_client.calcScore_x01([curDart, '-', '-'])
                                    self.dc_client.DC_enterScore_x01(score)
                            case 'Cricket':
                                self.dc_client.DC_enterScore_cricket([curDart, '-', '-'])

                    if self.AD_checkTurnEnd():
                        self.dc_client.DC_endTurn()
                        self.dc_client.DC_checkEndGame()
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
                app.dc_client.quit()
                app.autodarts_client.stop_event_stream()
                quit()
            case _:
                print('Invalid Input, Please Try Again!')

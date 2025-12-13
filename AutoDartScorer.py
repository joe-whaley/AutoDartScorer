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
from AutoDartsClient import AutodartsAPIClient, AutodartsConfig, _print_dart

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
        self.last_turn_state = "status:none"
        self.current_game_type = None
        self.doubled_in = False
        self.game_active = False
    
    def shutdown(self):
        """Cleanly stop event stream and close DartConnect browser."""
        try:
            self.autodarts_client.stop_event_stream()
        except Exception:
            pass
        try:
            self.dc_client.quit()
        except Exception:
            pass
    
    def handle_autodarts_event(self, event: dict):
        # Let AutoDartsClient translate the raw event into a turnState string
        turn_state = _print_dart(event)
        self.last_turn_state = turn_state

        # If no active game, ignore the event
        if not self.game_active:
            return

        # Handle dart events immediately (no polling needed)
        if turn_state and turn_state.startswith("dart:") and self.current_game_type:
            dart_code = turn_state.split(":", 1)[1].split()[0]
            self.current_throws = [dart_code, '-', '-']
            self.takeout_in_progress = False

            # Decide if this dart should be scored, accounting for 301 double-in
            should_score = True
            if self.current_game_type == '301':
                if not self.doubled_in:
                    self.doubled_in = (dart_code.startswith('D')) or (dart_code == 'Bull')
                should_score = self.doubled_in

            if should_score:
                self.dc_client.handle_turn_state(turn_state, self.current_game_type)

        # Handle turn end statuses
        if turn_state == "status:turnComplete": # TODO: Might just want a button to score turn/end game
            try:
                self.dc_client.DC_endTurn() # TODO: Might want to add score fix/override, or button to end turn
                self.dc_client.DC_checkEndGame() # TODO: checkEndGame isn't working, maybe just have button to end game
            except Exception:
                # If DartConnect interaction fails, assume game ended
                self.game_active = False
            self.takeout_in_progress = False
        elif turn_state == "status:turnEnding":
            # TODO: Set a timeout here to manually reset AutoDarts if it gets stuck here
            self.takeout_in_progress = True
        elif turn_state == "status:turnIncomplete":
            self.takeout_in_progress = False

    def playGame(self, gameType = ''):
        print('Now Playing ' + gameType + '...')
        print('GAME ON!')
        self.current_game_type = gameType
        self.doubled_in = False
        self.game_active = True
        # TODO: Might want to first check that WebSocket is connected, if not, restart AutoDartsClient and Start/Restart AutoDarts

        try:
            while self.game_active:
                # WebSocket callbacks will handle scoring; just idle
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.game_active = False
        finally:
            self.current_game_type = None



if __name__ == '__main__':
    app = AutoScorer()
    print('Welcome to AutoScorer!')
    print('Your DartConnect/AutoDarts Link!')
    while True:
        gameType = input('Enter 501, 301, Cricket, or Quit: ')
        match gameType:
            case '501' | '301' | 'Cricket':
                app.playGame(gameType)
                print('GAME OVER')
            case 'Training':
                # TODO: Implement Training Mode that saves throws to a file for later review
                print('Training Mode is not yet implemented. Please select another option.')
            case 'Quit':
                print('Thank you! Goodbye!')
                time.sleep(2)
                app.shutdown()
                quit()
            case _:
                print('Invalid Input, Please Try Again!')

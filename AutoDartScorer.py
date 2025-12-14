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
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog

from Clients import (
    AutodartsAPIClient,
    AutodartsConfig,
    DartConnectClient,
    TrainingClient,
    _print_dart,
)

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
        self.autodarts_cfg = AutodartsConfig(
            base_url=self.boardManager_AutoDarts,
            api_key=self.autodarts_api_key,
            board_id=self.autodarts_board_id,
        )
        self.autodarts_client = AutodartsAPIClient(self.autodarts_cfg)
        self.autodarts_client.on_event = self.handle_autodarts_event
        self.autodarts_client.start_event_stream()

        # Track latest autodarts state
        self.current_throws = ['-', '-', '-']
        self.takeout_in_progress = False
        self.last_turn_state = "status:none"
        self.current_game_type = None
        self.doubled_in = False
        self.game_active = False
        self.turn_timeout_start = None
        self.turn_timeout_seconds = 3
        self.training_log_path = "training_throws.csv"
        self.training_client = None
        self.current_dart_count = 0

        # GUI setup
        self.root = tk.Tk()
        self.root.title("Auto Dart Scorer")
        self.status_text = tk.StringVar(value="Idle - select a game and press Start")
        self.game_var = tk.StringVar(value="501")
        self._build_gui()
        self._schedule_watchdog()
    
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
            self.current_dart_count = min(self.current_dart_count + 1, 3)

            # Decide if this dart should be scored, accounting for 301 double-in
            should_score = True
            if self.current_game_type == '301':
                if not self.doubled_in:
                    self.doubled_in = (dart_code.startswith('D')) or (dart_code == 'Bull')
                should_score = self.doubled_in

            if self.current_game_type == 'Training':
                if self.training_client is not None:
                    error = self.training_client.log_throw(turn_state)
                    if error:
                        self._update_status(f"Failed to log training throw: {error}")
                    else:
                        self._update_status(f"Logged training throw: {turn_state}")
            elif should_score:
                self.dc_client.handle_turn_state(turn_state, self.current_game_type)

        # Handle turn end statuses
        if turn_state == "status:turnComplete":
            try:
                if self.current_game_type != 'Training':
                    self.dc_client.endTurn()
                    if self.dc_client.checkEndGame(self.current_dart_count):
                        self.game_active = False
                        self._update_status("Game finished in DartConnect.")
            except Exception:
                # If DartConnect interaction fails, assume game ended
                self.game_active = False
                self._update_status("Error ending turn; stopped game.")
            self.takeout_in_progress = False
            self.current_dart_count = 0
        elif turn_state == "status:turnEnding":
            self.takeout_in_progress = True
            self.turn_timeout_start = time.time()
        elif turn_state == "status:turnIncomplete":
            self.takeout_in_progress = False
            self.turn_timeout_start = None

    def playGame(self, gameType = ''):
        print('Now Playing ' + gameType + '...')
        print('GAME ON!')
        self.current_game_type = gameType
        self.doubled_in = False
        self.game_active = True
        self.autodarts_client.ensure_websocket()

        try:
            while self.game_active:
                # WebSocket callbacks will handle scoring; just idle
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.game_active = False
        finally:
            self.current_game_type = None

    # ---------------- GUI helpers ----------------

    def _build_gui(self):
        controls = tk.Frame(self.root, padx=10, pady=10)
        controls.pack(fill="both", expand=True)

        tk.Label(controls, text="Game Type:").grid(row=0, column=0, sticky="w")
        game_options = ["501", "301", "Cricket", "Training"]
        tk.OptionMenu(controls, self.game_var, *game_options).grid(row=0, column=1, sticky="we")

        tk.Button(controls, text="Start/Restart Game", command=self.start_selected_game).grid(row=0, column=2, padx=5, pady=2)
        tk.Button(controls, text="End Turn", command=self.manual_end_turn).grid(row=1, column=0, padx=5, pady=2, sticky="we")
        tk.Button(controls, text="End Game", command=self.stop_game).grid(row=1, column=1, padx=5, pady=2, sticky="we")
        tk.Button(controls, text="Start/Restart AutoDarts", command=self._ui_restart_autodarts).grid(row=1, column=2, padx=5, pady=2, sticky="we")

        status_frame = tk.Frame(self.root, padx=10, pady=10)
        status_frame.pack(fill="x")
        tk.Label(status_frame, text="Status:").pack(anchor="w")
        tk.Label(status_frame, textvariable=self.status_text, anchor="w", justify="left", wraplength=500).pack(fill="x")

    def _update_status(self, text: str):
        def _set():
            self.status_text.set(text)
        # Tkinter should only update from main thread
        if threading.current_thread() is threading.main_thread():
            _set()
        else:
            self.root.after(0, _set)

    def _schedule_watchdog(self):
        """Periodic watchdog to recover if takeout gets stuck and to keep GUI responsive."""
        self._check_turn_timeout()
        self.root.after(500, self._schedule_watchdog)

    def _check_turn_timeout(self):
        if self.takeout_in_progress and self.turn_timeout_start:
            elapsed = time.time() - self.turn_timeout_start
            if elapsed > self.turn_timeout_seconds:
                self.takeout_in_progress = False
                self.turn_timeout_start = None
                self._update_status("Turn timeout reached; ending turn manually.")
                try:
                    self.autodarts_client.restart_autodarts(on_event=self.handle_autodarts_event)
                    self.dc_client.endTurn()
                except Exception:
                    pass

    def start_selected_game(self):
        gameType = self.game_var.get()
        if gameType not in ['501', '301', 'Cricket', 'Training']:
            messagebox.showerror("Invalid Game", "Please select a valid game.")
            return
        self.start_game(gameType)

    def start_game(self, gameType: str):
        self.current_game_type = gameType
        self.doubled_in = False
        self.game_active = True
        self.takeout_in_progress = False
        self.turn_timeout_start = None
        self.autodarts_client.ensure_websocket()
        self._update_status(f"Game started: {gameType}")
        print(f"Now Playing {gameType}...\nGAME ON!")
        if gameType == 'Training':
            new_path = simpledialog.askstring(
                "Training Log",
                "Enter training log filename (e.g., training_throws.csv):",
                initialvalue=self.training_log_path,
                parent=self.root,
            )
            if not new_path:
                # User cancelled: abort training start
                self.game_active = False
                self.current_game_type = None
                self.current_dart_count = 0
                self._update_status("Training game cancelled.")
                return
            user_path = new_path.strip()
            base, ext = os.path.splitext(user_path)
            suffix = time.strftime("%Y%m%d%H%M%S")
            if not ext:
                ext = ".csv"
            self.training_log_path = f"{base}_{suffix}{ext}"
            if self.training_client is not None:
                try:
                    self.training_client.window.destroy()
                except Exception:
                    pass
            self.training_client = TrainingClient(self.training_log_path, master=self.root)
            self._update_status(f"Game started: {gameType} | logging to {self.training_log_path}")
        self.current_dart_count = 0

    def stop_game(self):
        self.game_active = False
        self.current_game_type = None
        self._update_status("Game stopped.")
        self.current_dart_count = 0
        try:
            if self.training_client is not None and getattr(self.training_client, "window", None):
                self.training_client.window.destroy()
        except Exception:
            pass
        self.training_client = None

    def manual_end_turn(self):
        if self.current_game_type == 'Training':
            self.takeout_in_progress = False
            self.turn_timeout_start = None
            self._update_status("Training turn marked complete.")
            self.current_dart_count = 0
            try:
                self.autodarts_client.restart_autodarts(on_event=self.handle_autodarts_event)
            except Exception:
                pass
            return

        try:
            self.dc_client.endTurn()
            if self.dc_client.checkEndGame(self.current_dart_count):
                self.game_active = False
                self._update_status("Game finished in DartConnect.")
            else:
                self._update_status("Turn ended manually.")
            self.current_dart_count = 0
        except Exception:
            self._update_status("Could not end turn; please check DartConnect.")
        finally:
            try:
                self.autodarts_client.restart_autodarts(on_event=self.handle_autodarts_event)
            except Exception:
                pass

    def _ui_restart_autodarts(self):
        self.autodarts_client.restart_autodarts(on_event=self.handle_autodarts_event)
        self._update_status("AutoDarts restarted and listening.")

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.shutdown()



if __name__ == '__main__':
    app = AutoScorer()
    print('Welcome to AutoScorer!')
    print('Your DartConnect/AutoDarts Link!')
    app.run()

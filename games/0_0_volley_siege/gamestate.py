from game_override import GameStateOverride
from src.calculations.scatter import Scatter

class GameState(GameStateOverride):
    """Gamestate for Volley Siege (Sticky Cell Multipliers in Free Spins)"""

    def __init__(self, config):
        super().__init__(config)
        # --- Define Grid Dimensions ---
        # 5 Rows, 6 Columns
        self.n_rows = 5 
        self.n_cols = 6 
        # -------------------------------------

    def init_multiplier_grid(self):
        """
        Helper: Resets the 6x5 Multiplier Grid to x1.
        We call this manually at the start of Base Game spins only.
        """
        self.multiplier_grid = [[1 for _ in range(self.n_cols)] for _ in range(self.n_rows)]

    def update_cell_multipliers(self):
        """
        Scans current wins and doubles the multiplier for winning coordinates.
        """
        if not self.win_data or "wins" not in self.win_data:
            return

        has_update = False
        
        for win in self.win_data["wins"]:
            for pos in win["positions"]:
                # --- Handle dictionary positions ---
                if isinstance(pos, dict):
                    # Try 'reel' first, fallback to 'col' if needed
                    c = pos.get("reel", pos.get("col"))
                    r = pos.get("row")
                else:
                    # Fallback for list/tuple [row, col]
                    r, c = pos[0], pos[1]
                
                # Ensure they are integers
                r, c = int(r), int(c)
                
                # Double the multiplier (x2, x4, x8...)
                self.multiplier_grid[r][c] *= 2
                has_update = True
        
        return has_update

    def emit_board_multiplier_info(self):
        """
        Sends the 'boardMultiplierInfo' event to the frontend.
        Also prints to the terminal for validation.
        """
        # 1. Sum only the ACTIVE multipliers (values > 1)
        raw_sum = sum(val for row in self.multiplier_grid for val in row if val > 1)
        
        # 2. Safety Check: If sum is 0 (no active multipliers), default to 1.
        total_mult = max(1, raw_sum)
        
        # --- DEBUG: VALIDATION PRINT ---
        if total_mult > 1:
            print(f"\n[VALIDATION] Sim {self.sim_index}: Multipliers Active! Total: x{total_mult}")
            for row in self.multiplier_grid:
                print(f"  {row}")
            print("-" * 30)
        # -------------------------------

        event_data = {
            "type": "boardMultiplierInfo",
            "winInfo": {
                "tumbleWin": self.win_data.get("totalWin", 0),
                "boardMult": total_mult,
                "totalWin": self.win_data.get("totalWin", 0),
                "multiplierMap": self.multiplier_grid 
            }
        }
        
        # Correctly append to the event list
        if hasattr(self.book, "events"):
            self.book.events.append(event_data)
        elif isinstance(self.book, dict):
            self.book["events"].append(event_data)

    def run_spin(self, sim: int, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        
        # Store sim index for debug printing
        self.sim_index = sim
        
        while self.repeat:
            self.reset_book()
            
            # --- BASE GAME RESET ---
            self.init_multiplier_grid()
            
            self.draw_board()

            # 1. Initial Evaluation
            self.get_scatterpays_update_wins()
            
            # 2. Update Multipliers (Initial Hit)
            if self.win_data["totalWin"] > 0:
                self.update_cell_multipliers()
                self.emit_board_multiplier_info()

            self.emit_tumble_win_events()

            # 3. Tumble Loop
            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                self.tumble_game_board()
                self.get_scatterpays_update_wins()
                
                # Update Multipliers (Tumble Hits)
                if self.win_data["totalWin"] > 0:
                    self.update_cell_multipliers()
                    self.emit_board_multiplier_info()
                
                self.emit_tumble_win_events()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        
        # --- FREE SPIN START ---
        # Multipliers persist from base game trigger
        
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.draw_board()

            # 1. Initial Evaluation (Free Spin)
            self.get_scatterpays_update_wins()
            
            if self.win_data["totalWin"] > 0:
                self.update_cell_multipliers()
                self.emit_board_multiplier_info()

            self.emit_tumble_win_events()

            # 2. Tumble Loop (Free Spin)
            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                self.tumble_game_board()
                
                self.get_scatterpays_update_wins()
                
                if self.win_data["totalWin"] > 0:
                    self.update_cell_multipliers()
                    self.emit_board_multiplier_info()
                
                self.emit_tumble_win_events()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()
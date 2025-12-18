"""
Game specific executable functions.
"""

from copy import copy
from game_calculations import GameCalculations
from src.calculations.scatter import Scatter
from src.events.events import (
    set_win_event,
    set_total_event,
    fs_trigger_event,
    update_tumble_win_event,
    update_freespin_event,
)

class GameExecutables(GameCalculations):
    """Game specific executable functions."""

    def set_end_tumble_event(self):
        """
        Calculates the final win for the spin by applying the Sticky Cell Multipliers.
        """
        # 1. Get the Board Multiplier from your sticky grid
        raw_sum = sum(val for row in self.multiplier_grid for val in row if val > 1)
        board_mult = max(1, raw_sum)

        # 2. Apply it to the spin win
        base_tumble_win = copy(self.win_manager.spin_win)
        
        # Only apply multiplier if it's greater than 1
        if board_mult > 1:
            self.win_manager.set_spin_win(base_tumble_win * board_mult)
            
            if self.win_manager.spin_win > 0:
                # --- FIXED: Manually construct event WITH the multiplierMap ---
                event_data = {
                    "type": "boardMultiplierInfo",
                    "winInfo": {
                        "tumbleWin": int(round(min(base_tumble_win, self.config.wincap) * 100)),
                        "boardMult": board_mult,
                        "totalWin": int(round(min(self.win_manager.spin_win, self.config.wincap) * 100)),
                        # CRITICAL: Include the grid so the frontend doesn't glitch!
                        "multiplierMap": self.multiplier_grid 
                    }
                }
                
                # Append to book events
                if hasattr(self.book, "events"):
                    self.book.events.append(event_data)
                elif isinstance(self.book, dict):
                    self.book["events"].append(event_data)
                # -------------------------------------------------------------

                update_tumble_win_event(self)

        # 3. Finalize Events
        if self.win_manager.spin_win > 0:
            set_win_event(self)
        set_total_event(self)

    def update_freespin_amount(self, scatter_key: str = "scatter"):
        """Update current and total freespin number and emit event."""
        self.tot_fs = self.count_special_symbols(scatter_key) * 2
        
        if self.gametype == self.config.basegame_type:
            basegame_trigger, freegame_trigger = True, False
        else:
            basegame_trigger, freegame_trigger = False, True
            
        fs_trigger_event(self, basegame_trigger=basegame_trigger, freegame_trigger=freegame_trigger)

    def get_scatterpays_update_wins(self):
        """Evaluate scatter wins."""
        # Note: We pass global_multiplier=1 because we apply our custom multiplier at the end
        self.win_data = Scatter.get_scatterpay_wins(
            self.config, self.board, global_multiplier=1
        )
        Scatter.record_scatter_wins(self)
        self.win_manager.tumble_win = self.win_data["totalWin"]
        self.win_manager.update_spinwin(self.win_data["totalWin"])

    def update_freespin(self) -> None:
        """Called before a new reveal during freegame."""
        self.fs += 1
        update_freespin_event(self)
        
        # We do NOT reset the multiplier grid here (it's sticky!)
        # We just reset the per-spin tracking variables
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}
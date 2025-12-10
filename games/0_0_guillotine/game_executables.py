from game_calculations import GameCalculations
from src.calculations.ways import Ways


class GameExecutables(GameCalculations):
    """Events specific to 'ways' wins"""

    def evaluate_ways_board(self):
        """Populate win-data, record wins, transmit events.
        OVERRIDE: Implements multiplicative logic for Wild multipliers.
        """
        # 1. Calculate standard ways wins (base amounts)
        self.win_data = Ways.get_ways_data(self.config, self.board)

        # 2. Apply multiplicative wild logic if wins exist
        if self.win_data["totalWin"] > 0:
            new_total_win = 0

            # Iterate through each distinct win (e.g., 3x H1, 4x H2)
            for win_entry in self.win_data.get("wins", []):
                compound_mult = 1  # multiplicative identity

                # Positions are dicts with reel/row indices
                for pos in win_entry.get("positions", []):
                    col, row = pos.get("reel"), pos.get("row")
                    if col is None or row is None:
                        continue
                    symbol_obj = self.board[col][row]

                    if symbol_obj.name in self.config.special_symbols.get("wild", []):
                        mult_val = symbol_obj.get_attribute("multiplier") if symbol_obj.check_attribute("multiplier") else 1
                        # Multiplicative (not additive) compounding
                        compound_mult *= max(1, mult_val)

                adjusted_win = win_entry["win"] * compound_mult
                win_entry["win"] = adjusted_win
                new_total_win += adjusted_win

            # 3. Update the global total win for the spin
            self.win_data["totalWin"] = new_total_win

            # 4. Record and update managers
            Ways.record_ways_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])

        # 5. Emit events
        Ways.emit_wayswin_events(self)

from game_executables import GameExecutables
from src.calculations.statistics import get_random_outcome
from src.events.events import reveal_event


class GameStateOverride(GameExecutables):
    """
    This class is is used to override or extend universal state.py functions.
    e.g: A specific game may have custom book properties to reset
    """

    def reset_book(self):
        # Reset global values used across multiple projects
        super().reset_book()
        # Reset parameters relevant to local game only

    def draw_board(self, emit_event: bool = True, trigger_symbol: str = "scatter"):
        """Draw board then clamp to a single scatter per reel before emitting events."""
        super().draw_board(emit_event=False, trigger_symbol=trigger_symbol)
        self.enforce_single_scatter_per_reel()
        # Refresh special-symbol cache after any replacements
        self.get_special_symbols_on_board()
        if emit_event:
            reveal_event(self)

    def enforce_single_scatter_per_reel(self, replacement_symbol: str = "L1") -> None:
        """Ensure no reel contains more than one scatter; replace extras with a non-special symbol."""
        scatter_names = set(self.config.special_symbols.get("scatter", []))
        for reel_idx, reel in enumerate(self.board):
            scatter_rows = [row for row, sym in enumerate(reel) if sym.name in scatter_names]
            if len(scatter_rows) > 1:
                # Keep the first scatter; replace the rest
                for row in scatter_rows[1:]:
                    self.board[reel_idx][row] = self.create_symbol(replacement_symbol)

    def assign_special_sym_function(self):
        self.special_symbol_functions = {"W": [self.assign_mult_property]}

    def assign_mult_property(self, symbol):
        """Assign symbol multiplier using probabilities defined in config distributions."""
        multiplier_value = get_random_outcome(self.get_current_distribution_conditions()["mult_values"])
        symbol.assign_attribute({"multiplier": multiplier_value})

    def check_game_repeat(self):
        """Verify final simulation outcomes satisfied all distribution/criteria conditions."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

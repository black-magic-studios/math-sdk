from game_executables import GameExecutables

class GameStateOverride(GameExecutables):
    """Override class for Guillotine."""

    def assign_special_sym_function(self):
        # No symbol-side assignment needed; guillotine logic handles wild/mult assignment
        self.special_symbol_functions = {}

    def draw_board(self, emit_event=True):
        super().draw_board(emit_event=False)

        # Enforce Max 1 Guillotine ('G') per reel immediately after draw
        for col in range(self.config.num_reels):
            g_count = 0
            for row in range(self.config.num_rows[col]):
                if self.board[col][row].name == "G":
                    g_count += 1
                    if g_count > 1:
                        # Replace extra Gs with L5
                        self.board[col][row] = self.create_symbol("L5")

        if emit_event:
            # Emit manually if needed, or pass
            pass

from game_calculations import GameCalculations
from src.calculations.lines import Lines
from src.calculations.statistics import get_random_outcome

class GameExecutables(GameCalculations):
    """Guillotine-specific executables: Jam/Drop, beheading, additive wild multipliers on lines."""

    def process_guillotine_features(self) -> None:
        """Resolve G symbols into wilds with assigned multipliers (Jam/Drop + beheading)."""
        guillotine_syms = self.config.special_symbols.get("guillotine", ["G"])
        highs = {"H1", "H2", "H3", "H4", "H5"}

        for reel_idx, reel in enumerate(self.board):
            g_rows = [r for r, sym in enumerate(reel) if sym.name in guillotine_syms]

            # Enforce max 1 G per reel (safety check)
            if len(g_rows) > 1:
                for extra_row in g_rows[1:]:
                    self.board[reel_idx][extra_row] = self.create_symbol("L5")
                g_rows = g_rows[:1]

            for g_row in g_rows:
                # True = Jam, False = Drop
                is_jam = get_random_outcome(self.config.guillotine_config["jam_drop_weights"])
                base_mult = get_random_outcome(self.config.guillotine_config["base_multiplier"])

                if is_jam:
                    # Jam: Single wild with base multiplier
                    self.board[reel_idx][g_row] = self.create_symbol("W")
                    self.board[reel_idx][g_row].assign_attribute({"multiplier": base_mult})
                    continue

                # Drop: convert the blade path to wilds
                path_rows = list(range(g_row, self.config.num_rows[reel_idx]))

                # Check for High Symbols (Beheading)
                hit_high = any(self.board[reel_idx][r].name in highs for r in path_rows)
                final_mult = base_mult
                if hit_high:
                    behead_mult = get_random_outcome(self.config.guillotine_config["behead_multiplier"])
                    final_mult = base_mult * behead_mult  # Multiplicative

                for r in path_rows:
                    self.board[reel_idx][r] = self.create_symbol("W")
                    self.board[reel_idx][r].assign_attribute({"multiplier": final_mult})

    def evaluate_lines_board(self):
        """Evaluate lines with additive wild multipliers."""
        # 1. Apply Guillotine resolution
        self.process_guillotine_features()

        # 2. Base line wins
        self.win_data = Lines.get_lines(
            self.board,
            self.config,
            wild_key="wild",
            wild_sym="W",
            multiplier_method="symbol",
            global_multiplier=self.global_multiplier,
        )

        # 3. Additive wild multiplier override
        if self.win_data["totalWin"] > 0:
            new_total = 0
            for win in self.win_data.get("wins", []):
                # Sum multipliers on wilds in the winning positions
                additive_mult = 0
                for pos in win.get("positions", []):
                    reel = pos.get("reel")
                    row = pos.get("row")
                    if reel is None or row is None:
                        continue
                    sym = self.board[reel][row]
                    if sym.name == "W" and sym.check_attribute("multiplier"):
                        additive_mult += sym.get_attribute("multiplier")

                # Default to 1x if no multipliers found
                total_multiplier = max(1, additive_mult)

                adjusted_win = win["win"] * total_multiplier
                win["win"] = adjusted_win
                win.setdefault("meta", {})["additiveMultiplier"] = total_multiplier
                win["meta"]["winWithoutMult"] = win["meta"].get("winWithoutMult", win["win"]/total_multiplier if total_multiplier else win["win"])
                new_total += adjusted_win

            self.win_data["totalWin"] = new_total
            Lines.record_lines_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])

        Lines.emit_linewin_events(self)

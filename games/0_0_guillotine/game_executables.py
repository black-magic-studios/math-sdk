"""Guillotine-specific executable helpers."""

from game_calculations import GameCalculations
from src.calculations.lines import Lines
from src.calculations.statistics import get_random_outcome


class GameExecutables(GameCalculations):
    """Guillotine executables: deterministic pre-eval resolution and per-reel multipliers."""

    def __init__(self, config):
        super().__init__(config)
        self.reel_multipliers = {}
        self.guillotine_resolved = False

    def _get_mode_config(self):
        """Return current mode settings based on current spin context.

        Preference order:
          1) Subclass get_current_mode_config(self) if present.
          2) Fallback to simple base/free switch plus self.bonus_mode.
        """
        # Prefer subclass-aware mode resolution when available (GameStateOverride)
        if hasattr(self, "get_current_mode_config"):
            cfg = self.get_current_mode_config(self)
            if cfg:
                return cfg

        # Fallback: treat anything with freegame_type gametype as free spins
        if getattr(self, "gametype", None) == getattr(self, "freegame_type", None):
            tier = getattr(self, "bonus_mode", "fs3")
            return self.config.bonus_modes.get(tier, self.config.bonus_modes["fs3"])

        # Default to base game config
        return self.config.bonus_modes["base"]

    def _draw_weighted_mult(self, weights_table):
        """Draw a multiplier from the discrete set using a weight table."""
        normalized = {m: float(weights_table.get(m, 0)) for m in self.config.multiplier_set}
        return get_random_outcome(normalized)

    def resolve_guillotines(self, mode_cfg=None):
        """Resolve G symbols into wilds and attach per-reel multipliers (pre-evaluation).

        mode_cfg:
            Optional explicit mode configuration (base/fs3/fs4/fs5). If not supplied,
            falls back to the current spin context via _get_mode_config().
        """
        guillotine_syms = self.config.special_symbols.get("guillotine", ["G"])
        scatter_syms = self.config.special_symbols.get("scatter", ["S"])
        highs = set(
            sym[1]
            for sym in self.config.paytable.keys()
            if isinstance(sym, tuple) and str(sym[1]).startswith("H")
        )

        if mode_cfg is None:
            mode_cfg = self._get_mode_config()

        self.reel_multipliers = {}
        self.guillotine_resolved = True

        for reel_idx, reel in enumerate(self.board):
            # Enforce max 1 S per reel (keep first occurrence on the visible grid)
            s_rows = [r for r, sym in enumerate(reel) if sym.name in scatter_syms]
            if len(s_rows) > 1:
                for extra_row in s_rows[1:]:
                    self.board[reel_idx][extra_row] = self.create_symbol("L5")

            # Find all Gs currently visible on this reel
            g_rows = [r for r, sym in enumerate(reel) if sym.name in guillotine_syms]

            # Enforce max 1 G per reel (keep first occurrence on the visible grid)
            if len(g_rows) > 1:
                for extra_row in g_rows[1:]:
                    self.board[reel_idx][extra_row] = self.create_symbol("L5")
                g_rows = g_rows[:1]

            if not g_rows:
                continue

            # Check Wild Capability (SSWCAP)
            # If capability is defined and this reel's capability symbol is NOT 'P', skip expansion.
            capability = getattr(self, "wild_capability", None)
            if capability and len(capability) > reel_idx:
                if capability[reel_idx] != "P":
                    continue # Skip expansion for this reel

            g_row = g_rows[0]

            # Jam check (only in modes that allow jam, that is base game)
            if mode_cfg.get("jam_allowed", False):
                jam_or_drop = get_random_outcome(self.config.jam_weights)
                if jam_or_drop == "jam":
                    # Jam: leave symbols as-is, no wilds created, no multiplier applied
                    continue

            # Drop path is strictly below G on this reel
            path_rows = list(range(g_row + 1, self.config.num_rows[reel_idx]))

            # Base multiplier for this reel (e.g. 2x, 5x, 10x...)
            g_mult = self._draw_weighted_mult(self.config.g_mult_weights)

            # Collect behead multipliers from high symbols in the drop path
            behead_vals = []
            for r in path_rows:
                sym = self.board[reel_idx][r]
                if sym.name in highs:
                    weights = self.config.symbol_behead_weights.get(
                        sym.name,
                        self.config.symbol_behead_weights.get("H1", {}),
                    )
                    behead_vals.append(self._draw_weighted_mult(weights))

            # Apply additive or multiplicative combination for this mode
            if mode_cfg.get("behead_mode", "ADD").upper() == "MULTIPLY":
                total_mult = g_mult
                for val in behead_vals:
                    total_mult *= val
            else:
                total_mult = g_mult + sum(behead_vals)

            # Convert G and its drop path into wilds carrying the reel multiplier marker.
            # Low symbols (L*) become wilds with no extra contribution; they just inherit total_mult.
            affected_rows = [g_row] + path_rows
            for r in affected_rows:
                self.board[reel_idx][r] = self.create_symbol("W")
                self.board[reel_idx][r].assign_attribute({"reel_multiplier": total_mult})

            # Track per-reel multiplier (applied once per line per reel)
            self.reel_multipliers[reel_idx] = total_mult

        # Refresh special symbols count after potential modifications (S/G removal, W creation)
        self.get_special_symbols_on_board()

    def evaluate_lines_board(self):
        """Evaluate lines after deterministic Guillotine resolution with per-reel multipliers."""
        if not getattr(self, "guillotine_resolved", False):
            self.resolve_guillotines()

        # Core line evaluation where wilds already carry any reel multipliers
        self.win_data = Lines.get_lines(
            self.board,
            self.config,
            wild_key="wild",
            wild_sym="W",
            multiplier_method="symbol",
            global_multiplier=self.global_multiplier,
        )

        if self.win_data["totalWin"] > 0:
            new_total = 0
            for win in self.win_data.get("wins", []):
                reels_with_mult = set()

                # Collect which reels in this line contain wilds with reel_multiplier
                for pos in win.get("positions", []):
                    reel = pos.get("reel")
                    row = pos.get("row")
                    if reel is None or row is None:
                        continue
                    sym = self.board[reel][row]
                    if sym.name == "W" and sym.check_attribute("reel_multiplier"):
                        reels_with_mult.add(reel)

                # Apply at most one reel multiplier per line to avoid multiplicative blow-up
                if reels_with_mult:
                    combined_mult = max(self.reel_multipliers.get(r, 1) for r in reels_with_mult)
                else:
                    combined_mult = 1

                adjusted_win = win["win"] * combined_mult
                # Clamp individual line wins to the wincap to prevent runaway payouts
                adjusted_win = min(adjusted_win, self.config.wincap)

                win["win"] = adjusted_win
                win.setdefault("meta", {})["reelMultipliers"] = {
                    str(r + 1): self.reel_multipliers.get(r, 1)
                    for r in sorted(reels_with_mult)
                }
                new_total += adjusted_win

            # Ensure total win respects wincap and spin accounting
            self.win_data["totalWin"] = min(new_total, self.config.wincap)
            Lines.record_lines_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])

        Lines.emit_linewin_events(self)

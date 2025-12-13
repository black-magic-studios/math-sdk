"""Overrides and helpers for Guillotine game logic."""

import random
from src.calculations.statistics import get_random_outcome
from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extend base executables with Guillotine-specific behaviour."""

    def __init__(self, config):
        super().__init__(config)
        self.reels = getattr(self.config, "reels", {})
        self.gametype = None
        self.board = []
        self.reel_positions = []
        self.anticipation = []

    # --- REQUIRED ABSTRACT METHODS (SDK CONTRACT) ---
    def assign_special_sym_function(self):
        """Map special symbols (like wilds) to their handlers."""
        self.special_symbol_functions = {"W": [self.assign_mult_property]}

    def assign_mult_property(self, symbol):
        """Placeholder hook for symbol multiplier assignment."""
        _ = symbol  # explicit no-op

    def run_spin(self, sim, simulation_seed=None):
        """Entry point for base-game spins with SDK signature compatibility."""
        state = None
        if isinstance(sim, (int, float)):
            self.reset_seed(sim, simulation_seed)
            self.reset_book()
            self.gametype = self.config.basegame_type
        else:
            state = sim
            # Ensure base-game context when called with external state
            self.gametype = getattr(self.config, "basegame_type", "base")
        return self.spin_logic(state)

    def run_freespin(self):
        """Entry point for free-spin runs; delegates to shared spin logic."""
        self.gametype = self.config.freegame_type
        return self.spin_logic(None)

    # --- MODE SELECTION ---
    def get_current_mode_config(self, state):
        """Select bonus-mode config based on betmode, gametype, and trigger count."""
        trigger_count = getattr(state, "fs_trigger_count", 0) if state else getattr(self, "fs_trigger_count", 0)

        # If betmode explicitly picks a tier, honor it
        if getattr(self, "betmode", "") in ("fs3", "fs4", "fs5"):
            return self.config.bonus_modes.get(self.betmode, self.config.bonus_modes.get("base", {}))

        # During freegame spins, use stored trigger count to select tier
        if getattr(self, "gametype", None) == self.config.freegame_type:
            if trigger_count >= 5:
                return self.config.bonus_modes.get("fs5", {})
            if trigger_count == 4:
                return self.config.bonus_modes.get("fs4", {})
            return self.config.bonus_modes.get("fs3", {})

        return self.config.bonus_modes.get("base", {})

    # --- MAIN GUILLOTINE LOGIC (SHARED SPIN FLOW) ---
    def spin_logic(self, state):
        """Centralized logic for both Base and Free spins."""
        self.guillotine_resolved = False
        self.reel_multipliers = {}

        mode_config = self.get_current_mode_config(state)
        guaranteed_g = mode_config.get("guaranteed_g", False)
        force_g_chance = mode_config.get("force_g_chance", 0.0)

        self.draw_board(
            emit_event=False,
            guaranteed_g=guaranteed_g,
            force_g_chance=force_g_chance,
            state=state,
        )
        self.resolve_guillotine_features(state, mode_config)
        self.calculate_wins(state)
        self._sync_state_view(state)
        return state

    def draw_board(self, emit_event=True, trigger_symbol="scatter", **kwargs):
        """Draw the board, optionally guaranteeing a guillotine symbol."""
        guaranteed_g = kwargs.get("guaranteed_g", False)
        force_g_chance = kwargs.get("force_g_chance", 0.0)
        state = kwargs.get("state")
        
        if isinstance(self.reels, list) and self.reels:
            self._draw_from_manual_reels(guaranteed_g)
        else:
            super().draw_board(emit_event=emit_event, trigger_symbol=trigger_symbol)
            
            # -------------------------------------------------------
            # OVERLAY LOGIC: P -> G
            # -------------------------------------------------------
            # Determine which overlay reel to use
            mode_config = self.get_current_mode_config(state)
            overlay_reels_cfg = mode_config.get("overlay_reels", {})
            
            # Resolve reel map based on gametype
            reels_map = overlay_reels_cfg.get(self.gametype, {})
            
            if reels_map:
                # Pick one reel file
                reel_name = get_random_outcome(reels_map)
                
                if reel_name and reel_name in self.reels:
                    overlay_strip = self.reels[reel_name]
                    # Pick stops for the overlay reel
                    stops = [random.randrange(len(overlay_strip[i])) for i in range(self.config.num_reels)]
                    
                    # Apply overlay
                    for r_idx in range(self.config.num_reels):
                        stop = stops[r_idx]
                        col_len = len(overlay_strip[r_idx])
                        for row in range(self.config.num_rows[r_idx]):
                            sym_id = overlay_strip[r_idx][(stop + row) % col_len]
                            if sym_id == "P":
                                self.board[r_idx][row] = self.create_symbol("G")

            # -------------------------------------------------------
            # WILD CAPABILITY LOGIC: SSWCAP
            # -------------------------------------------------------
            # Read SSWCAP reel to determine valid expansion columns.
            sswcap_reel = self.config.reels.get("SSWCAP")
            if sswcap_reel:
                # Pick a random stop for the capability reel
                # Assuming all reels in SSWCAP have same length, pick one stop for all? 
                # Or independent stops? Usually independent.
                # But "Layered ExpWilds" often uses a single strip or independent.
                # Let's assume independent stops like normal reels.
                cap_stops = [random.randrange(len(sswcap_reel[i])) for i in range(self.config.num_reels)]
                
                self.wild_capability = []
                for r_idx in range(self.config.num_reels):
                    # Get symbol at stop for this reel (top row)
                    cap_sym = sswcap_reel[r_idx][cap_stops[r_idx] % len(sswcap_reel[r_idx])]
                    self.wild_capability.append(cap_sym)
            else:
                self.wild_capability = ["P"] * self.config.num_reels 

            # Ensure guarantee/force logic applies in the normal reel path.
            self._ensure_guillotine_symbol(guaranteed_g)
            self._maybe_force_guillotine(force_g_chance)

        self._sync_state_view(state)

    def resolve_guillotine_features(self, state, mode_config):
        """Resolve guillotine drop/jam mechanics before evaluating wins."""
        self.guillotine_resolved = False
        self.resolve_guillotines(mode_cfg=mode_config)
        self._sync_state_view(state)

    def calculate_wins(self, state):
        """Evaluate wins and propagate multipliers to the external state."""
        self.evaluate_lines_board()
        if state is not None:
            state.reel_multipliers = [
                self.reel_multipliers.get(i, 1) for i in range(self.config.num_reels)
            ]
            state.win_data = getattr(self, "win_data", {})

    # --- HELPERS ---
    def _draw_from_manual_reels(self, guaranteed_g=False):
        """Use manually injected reelstrips (for verification scripts)."""
        self.refresh_special_syms()
        board = [[] for _ in range(self.config.num_reels)]
        reel_positions = [0] * self.config.num_reels

        for reel_idx in range(self.config.num_reels):
            reel_strip = self.reels[reel_idx]
            stop = random.randrange(0, len(reel_strip))
            reel_positions[reel_idx] = stop
            column = []
            for row in range(self.config.num_rows[reel_idx]):
                sym_id = reel_strip[(stop + row) % len(reel_strip)]
                column.append(self.create_symbol(sym_id))
            board[reel_idx] = column

        self.board = board
        self.reel_positions = reel_positions
        self.anticipation = [0] * self.config.num_reels
        self._ensure_guillotine_symbol(guaranteed_g)
        self.get_special_symbols_on_board()

    def _ensure_guillotine_symbol(self, guaranteed_g):
        """Force at least one guillotine symbol onto the board when required."""
        if not guaranteed_g:
            return

        guillotine_syms = self.config.special_symbols.get("guillotine", ["G"])
        if any(
            sym.name in guillotine_syms
            for reel in getattr(self, "board", [])
            for sym in reel
        ):
            return

        reel_idx = random.randrange(self.config.num_reels)
        row_idx = random.randrange(self.config.num_rows[reel_idx])
        self.board[reel_idx][row_idx] = self.create_symbol(guillotine_syms[0])

    def _sync_state_view(self, state):
        """Expose a lightweight view of the board to external callers."""
        if state is None:
            return

        state.grid = [[sym.name for sym in reel] for reel in getattr(self, "board", [])]
        state.stops = getattr(self, "reel_positions", [])
        state.reel_multipliers = [
            self.reel_multipliers.get(i, 1) for i in range(self.config.num_reels)
        ]

    def _maybe_force_guillotine(self, force_g_chance: float) -> None:
        """Inject a guillotine if absent, gated by probability."""
        if force_g_chance <= 0:
            return

        if any(sym.name in self.config.special_symbols.get("guillotine", ["G"]) for reel in self.board for sym in reel):
            return

        if random.random() < force_g_chance:
            self._ensure_guillotine_symbol(True)

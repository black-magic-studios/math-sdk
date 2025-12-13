from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Handle basegame and freegame logic for the Guillotine 5x4 lines game."""

    def run_spin(self, sim: int, simulation_seed=None) -> None:
        """Standard basegame loop used by the SDK simulation runner."""
        self.reset_seed(sim)
        self.repeat = True

        while self.repeat:
            self.reset_book()
            self.guillotine_resolved = False
            self.reel_multipliers = {}

            # Determine current mode (base or fs tier) and whether G is guaranteed
            mode_config = self.get_current_mode_config(self)
            guaranteed_g = mode_config.get("guaranteed_g", False)

            # Draw grid, optionally enforcing at least one G in FS4/FS5
            self.draw_board(emit_event=True, guaranteed_g=guaranteed_g)

            # Resolve Guillotines and evaluate lines
            self.evaluate_lines_board()

            # Track wins by gametype
            self.win_manager.update_gametype_wins(self.gametype)

            # Stop early if wincap reached to avoid runaway loops
            if self.evaluate_wincap():
                break

            # Check and enter free spins when scatter condition met
            if self.check_fs_condition() and self.check_freespin_entry():
                self.fs_trigger_count = self.count_special_symbols("scatter")
                self.run_freespin_from_base()

            # Final win handling and repeat control
            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self) -> None:
        """Free spin loop including retriggers."""
        self.reset_fs_spin()

        while self.fs < self.tot_fs:
            self.update_freespin()
            self.guillotine_resolved = False
            self.reel_multipliers = {}

            # Determine FS tier (fs3/fs4/fs5) and guaranteed G flag
            mode_config = self.get_current_mode_config(self)
            guaranteed_g = mode_config.get("guaranteed_g", False)

            # Draw grid with correct Guillotine guarantee for FS4/FS5
            self.draw_board(emit_event=True, guaranteed_g=guaranteed_g)

            # Resolve Guillotines and evaluate lines
            self.evaluate_lines_board()

            # Handle retriggers if scatters land during free spins
            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

            self.win_manager.update_gametype_wins(self.gametype)

            # End free spins early once the win cap is hit
            if self.evaluate_wincap():
                break

        self.end_freespin()

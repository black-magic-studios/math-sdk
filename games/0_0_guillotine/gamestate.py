from game_override import GameStateOverride

class GameState(GameStateOverride):
    """Handle basegame and freegame logic for Lines game."""

    def run_spin(self, sim: int, simulation_seed=None) -> None:
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)

            # CHANGED: Call Lines Evaluation
            self.evaluate_lines_board()

            self.win_manager.update_gametype_wins(self.gametype)
            
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self) -> None:
        self.reset_fs_spin()
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.draw_board(emit_event=True)

            # CHANGED: Call Lines Evaluation
            self.evaluate_lines_board()

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()
            self.win_manager.update_gametype_wins(self.gametype)
        self.end_freespin()

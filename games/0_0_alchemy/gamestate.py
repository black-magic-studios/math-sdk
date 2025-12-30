from game_override import GameStateOverride
from game_events import update_grid_mult_event


# Global stats tracking for detailed logging
class SimulationStats:
    """Track detailed simulation statistics."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.total_spins = 0
        self.base_spins = 0  # Only base game spins (for trigger rate)
        self.total_freespin_triggers = 0
        self.total_freespins_played = 0
        self.scatter_near_misses = 0  # 3 scatters (one short of trigger)
        self.scatter_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
        self.highest_multiplier = 0
        self.highest_win = 0
        self.wincap_hits = 0
        self.total_tumbles = 0
        self.max_tumbles_in_spin = 0
        self.retriggers = 0
        self.total_base_win = 0
        self.total_fs_win = 0
        self.highest_grid_mult = 0
        self.cluster_sizes = {}  # Track cluster size frequency
        self.wins_by_symbol = {}  # Track wins per symbol
        # Feature tracking
        self.wild_potion_triggers = 0
        self.elixir_bomb_triggers = 0
        self.symbol_transform_triggers = 0
    
    def print_stats(self, mode_name=""):
        print(f"\n{'='*60}")
        print(f"  DETAILED SIMULATION STATS - {mode_name}")
        print(f"{'='*60}")
        print("\n--- Spin Statistics ---")
        print(f"  Total spins: {self.total_spins}")
        print(f"  Total tumbles: {self.total_tumbles}")
        print(f"  Max tumbles in single spin: {self.max_tumbles_in_spin}")
        
        print("\n--- Scatter Distribution ---")
        for count, freq in sorted(self.scatter_counts.items()):
            pct = (freq / max(self.total_spins, 1)) * 100
            print(f"  {count} scatters: {freq} times ({pct:.2f}%)")
        
        print("\n--- Near Miss & Trigger Stats ---")
        print(f"  Scatter near misses (3 scatters): {self.scatter_near_misses}")
        print(f"  Freespin triggers: {self.total_freespin_triggers}")
        if self.total_freespin_triggers > 0:
            trigger_1_in = self.base_spins / self.total_freespin_triggers
            print(f"  Trigger rate: 1 in {trigger_1_in:.1f} base spins")
        near_miss_rate = (self.scatter_near_misses / max(self.base_spins, 1)) * 100
        print(f"  Near miss rate: {near_miss_rate:.2f}%")
        
        print("\n--- Alchemy Features ---")
        print(f"  Wild Potion triggers: {self.wild_potion_triggers}")
        print(f"  Elixir Bomb triggers: {self.elixir_bomb_triggers}")
        print(f"  Symbol Transform triggers: {self.symbol_transform_triggers}")
        
        print("\n--- Freespin Statistics ---")
        print(f"  Total freespins played: {self.total_freespins_played}")
        print(f"  Retriggers: {self.retriggers}")
        if self.total_freespin_triggers > 0:
            avg_fs = self.total_freespins_played / self.total_freespin_triggers
            print(f"  Avg freespins per trigger: {avg_fs:.1f}")
        
        print("\n--- Win Statistics ---")
        print(f"  Highest single win: {self.highest_win:.2f}x")
        print(f"  Highest grid multiplier: {self.highest_grid_mult}x")
        print(f"  Wincap hits (5000x): {self.wincap_hits}")
        print(f"  Total base game win: {self.total_base_win:.2f}")
        print(f"  Total freespin win: {self.total_fs_win:.2f}")
        
        # Calculate RTP breakdown (wagered = base_spins * stake)
        total_wagered = self.base_spins  # Assuming stake = 1
        base_rtp = (self.total_base_win / total_wagered * 100) if total_wagered > 0 else 0
        fs_rtp = (self.total_fs_win / total_wagered * 100) if total_wagered > 0 else 0
        total_rtp = base_rtp + fs_rtp
        print("\n--- RTP Breakdown ---")
        print(f"  Base spins: {self.base_spins}")
        print(f"  Base Game RTP: {base_rtp:.2f}%")
        print(f"  Free Spins RTP: {fs_rtp:.2f}%")
        print(f"  Total RTP: {total_rtp:.2f}%")
        
        if self.cluster_sizes:
            print("\n--- Cluster Size Distribution ---")
            for size, count in sorted(self.cluster_sizes.items()):
                print(f"  Size {size}: {count} clusters")
        
        if self.wins_by_symbol:
            print("\n--- Wins by Symbol ---")
            for sym, total in sorted(self.wins_by_symbol.items(), key=lambda x: -x[1]):
                print(f"  {sym}: {total:.2f}")
        
        print(f"\n{'='*60}\n")


# Global stats instance
sim_stats = SimulationStats()


class GameState(GameStateOverride):
    """Core function handling simulation results."""

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            # Reset simulation variables and draw a new board based on the betmode criteria.
            self.reset_book()
            self.draw_board()
            update_grid_mult_event(self)
            
            # Track scatter count for this spin
            scatter_count = self.count_special_symbols("scatter")
            sim_stats.scatter_counts[min(scatter_count, 7)] += 1
            
            # Check for TRUE near miss: 3 scatters where the 3rd lands before the last reel
            # (meaning there were remaining reels that could have had the 4th)
            if scatter_count == 3:
                if self._is_true_near_miss():
                    sim_stats.scatter_near_misses += 1
            
            sim_stats.total_spins += 1
            sim_stats.base_spins += 1  # Track base game spins separately
            tumbles_this_spin = 0

            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
            self.update_grid_mults()
            self._track_win_stats()

            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                tumbles_this_spin += 1
                sim_stats.total_tumbles += 1
                self.tumble_game_board()
                self.get_clusters_update_wins()
                self.emit_tumble_win_events()
                self.update_grid_mults()
                self._track_win_stats()
            
            # After tumbles end, check for alchemy features
            if not self.wincap_triggered:
                self._apply_features_after_tumbles()
            
            sim_stats.max_tumbles_in_spin = max(sim_stats.max_tumbles_in_spin, tumbles_this_spin)
            self._track_grid_mult()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition() and self.check_freespin_entry():
                sim_stats.total_freespin_triggers += 1
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            
            # Track final win
            if hasattr(self, 'final_win'):
                sim_stats.highest_win = max(sim_stats.highest_win, self.final_win)
                if self.final_win >= 5000:
                    sim_stats.wincap_hits += 1
            
            self.check_repeat()

        self.imprint_wins()
        
        # Track base/fs wins
        sim_stats.total_base_win += self.win_manager.basegame_wins
        sim_stats.total_fs_win += self.win_manager.freegame_wins

    def run_freespin(self):
        self.reset_fs_spin()
        
        while self.fs < self.tot_fs:
            self.update_freespin()
            sim_stats.total_freespins_played += 1
            
            self.draw_board()
            update_grid_mult_event(self)
            
            # Track scatter count during freespins
            scatter_count = self.count_special_symbols("scatter")
            if scatter_count == 2:  # Near miss for retrigger (need 3)
                pass  # Could track FS near misses separately

            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
            self.update_grid_mults()
            self._track_win_stats()
            
            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                sim_stats.total_tumbles += 1
                self.tumble_game_board()
                self.get_clusters_update_wins()
                self.emit_tumble_win_events()
                self.update_grid_mults()
                self._track_win_stats()
            
            # After tumbles end, check for alchemy features (higher chance in freespins)
            if not self.wincap_triggered:
                self._apply_features_after_tumbles()
            
            self._track_grid_mult()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition():
                sim_stats.retriggers += 1
                self.update_fs_retrigger_amt()

        self.end_freespin()
    
    def _apply_features_after_tumbles(self):
        """
        Apply alchemy features after tumbles end.
        Features are symbol-based: they trigger when P, B, or T symbols are on the board.
        Features can re-trigger tumbles if they create new wins.
        """
        # Get feature symbols currently on board
        potion_positions = self.special_syms_on_board.get("potion", [])
        transform_positions = self.special_syms_on_board.get("transform", [])
        bomb_positions = self.special_syms_on_board.get("bomb", [])
        
        feature_applied = False
        
        # Apply Wild Potion if P symbols present
        if potion_positions:
            self.apply_wild_potion(potion_positions)
            sim_stats.wild_potion_triggers += len(potion_positions)
            feature_applied = True
        
        # Apply Symbol Transform if T symbols present
        if transform_positions:
            self.apply_symbol_transform(transform_positions)
            sim_stats.symbol_transform_triggers += len(transform_positions)
            feature_applied = True
        
        # Apply Elixir Bomb if B symbols present (triggers tumble)
        if bomb_positions:
            self.apply_elixir_bomb(bomb_positions)
            sim_stats.elixir_bomb_triggers += len(bomb_positions)
            # Bomb causes symbols to explode, need to tumble
            self.tumble_game_board()
            feature_applied = True
        
        # If any feature applied, re-evaluate for wins
        if feature_applied:
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
            self.update_grid_mults()
            self._track_win_stats()
            
            # Continue tumbling if there are wins
            while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
                sim_stats.total_tumbles += 1
                self.tumble_game_board()
                self.get_clusters_update_wins()
                self.emit_tumble_win_events()
                self.update_grid_mults()
                self._track_win_stats()
    
    def _is_true_near_miss(self):
        """
        Check if this is a TRUE near miss:
        - Exactly 3 scatters on the board
        - The rightmost (last) scatter is NOT on the final reel
        - This means there were remaining reels that could have had the 4th scatter
        """
        scatter_positions = self.special_syms_on_board.get("scatter", [])
        if len(scatter_positions) != 3:
            return False
        
        # Find the rightmost reel that has a scatter
        rightmost_scatter_reel = max(pos["reel"] for pos in scatter_positions)
        
        # It's a true near miss if the 3rd scatter landed before the last reel
        # (leaving at least one reel that could have had the 4th)
        last_reel_index = self.config.num_reels - 1  # 6 for a 7-reel game
        return rightmost_scatter_reel < last_reel_index
    
    def _track_win_stats(self):
        """Track detailed win statistics."""
        if hasattr(self, 'win_data') and self.win_data.get("wins"):
            for win in self.win_data["wins"]:
                # Track cluster sizes
                cluster_size = win.get("clusterSize", 0)
                if cluster_size > 0:
                    sim_stats.cluster_sizes[cluster_size] = sim_stats.cluster_sizes.get(cluster_size, 0) + 1
                
                # Track wins by symbol
                symbol = win.get("symbol", "unknown")
                win_amt = win.get("win", 0)
                sim_stats.wins_by_symbol[symbol] = sim_stats.wins_by_symbol.get(symbol, 0) + win_amt
    
    def _track_grid_mult(self):
        """Track highest grid multiplier."""
        if hasattr(self, 'position_multipliers'):
            for reel in self.position_multipliers:
                for mult in reel:
                    if mult > sim_stats.highest_grid_mult:
                        sim_stats.highest_grid_mult = mult

from game_calculations import GameCalculations
from src.calculations.cluster import Cluster
from game_events import (
    update_grid_mult_event,
    wild_potion_event,
    elixir_bomb_event,
    symbol_transform_event,
)
from src.events.events import update_freespin_event
import random


class GameExecutables(GameCalculations):
    """Game dependent grouped functions."""

    def reset_grid_mults(self):
        """Initialize all grid position multipliers."""
        self.position_multipliers = [
            [1 for _ in range(self.config.num_rows[reel])] for reel in range(self.config.num_reels)
        ]

    def update_grid_mults(self):
        """All positions start with 1x. If there is a win in that position, the grid point
        multiplier DOUBLES for subsequent wins on that position."""
        if self.win_data["totalWin"] > 0:
            for win in self.win_data["wins"]:
                for pos in win["positions"]:
                    # Double the multiplier (starts at 1x, then 2x, 4x, 8x, etc.)
                    self.position_multipliers[pos["reel"]][pos["row"]] *= 2
                    self.position_multipliers[pos["reel"]][pos["row"]] = min(
                        self.position_multipliers[pos["reel"]][pos["row"]], self.config.maximum_board_mult
                    )
            update_grid_mult_event(self)

    def get_clusters_update_wins(self):
        """Find clusters on board and update win manager."""
        clusters = Cluster.get_clusters(self.board, "wild")
        return_data = {
            "totalWin": 0,
            "wins": [],
        }
        self.board, self.win_data = self.evaluate_clusters_with_grid(
            config=self.config,
            board=self.board,
            clusters=clusters,
            pos_mult_grid=self.position_multipliers,
            global_multiplier=self.global_multiplier,
            return_data=return_data,
        )

        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    def update_freespin(self) -> None:
        """Called before a new reveal during freegame."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.tumblewin_mult = 0
        self.win_data = {}

    # ===== ALCHEMY FEATURES (Symbol-Based) =====
    
    def check_and_apply_features(self):
        """
        Check for feature symbols on the board and apply their effects.
        Features trigger based on symbols present, not random probability.
        Returns True if any feature was applied (to continue tumbling).
        """
        feature_applied = False
        
        # Check for Potion symbols (P) - adds wilds
        potion_positions = self.special_syms_on_board.get("potion", [])
        if potion_positions:
            self.apply_wild_potion(potion_positions)
            feature_applied = True
        
        # Check for Transform symbols (T) - transforms other symbols
        transform_positions = self.special_syms_on_board.get("transform", [])
        if transform_positions:
            self.apply_symbol_transform(transform_positions)
            feature_applied = True
        
        # Check for Bomb symbols (B) - explodes area
        bomb_positions = self.special_syms_on_board.get("bomb", [])
        if bomb_positions:
            self.apply_elixir_bomb(bomb_positions)
            # Bomb causes symbols to explode, need to tumble
            self.tumble_game_board()
            feature_applied = True
        
        return feature_applied
    
    def apply_wild_potion(self, potion_positions=None):
        """
        Wild Potion Feature (Symbol-Based):
        Each Potion symbol (P) on the board adds 1-5 wilds at random positions.
        The potion symbol itself is then removed.
        """
        if potion_positions is None:
            potion_positions = self.special_syms_on_board.get("potion", [])
        
        if not potion_positions:
            return
        
        all_wild_positions = []
        
        for potion_pos in potion_positions:
            min_wilds, max_wilds = self.config.wild_potion_range
            # 40% chance of a "dud" potion that adds 0 wilds
            # Features should sometimes feel worthless
            if random.random() < 0.4:
                num_wilds = 0
            else:
                num_wilds = random.randint(min_wilds, max_wilds)
            
            # Find all valid positions (not wild, not scatter, not feature symbols)
            valid_positions = []
            for reel in range(self.config.num_reels):
                for row in range(self.config.num_rows[reel]):
                    sym = self.board[reel][row]
                    if not sym.check_attribute("wild", "scatter", "potion", "bomb", "transform"):
                        valid_positions.append((reel, row))
            
            # Randomly select positions to place wilds
            if valid_positions:
                num_to_place = min(num_wilds, len(valid_positions))
                selected_positions = random.sample(valid_positions, num_to_place)
                
                for reel, row in selected_positions:
                    self.board[reel][row] = self.create_symbol("W")
                    all_wild_positions.append({"reel": reel, "row": row})
                    
                    # Update special symbols tracking
                    if "wild" not in self.special_syms_on_board:
                        self.special_syms_on_board["wild"] = []
                    self.special_syms_on_board["wild"].append({"reel": reel, "row": row})
            
            # Mark the potion symbol for removal
            self.board[potion_pos["reel"]][potion_pos["row"]].explode = True
        
        # Clear potion tracking
        self.special_syms_on_board["potion"] = []
        
        # Emit event for frontend
        if all_wild_positions:
            wild_potion_event(self, all_wild_positions)
    
    def apply_elixir_bomb(self, bomb_positions=None):
        """
        Elixir Bomb Feature (Symbol-Based):
        Each Bomb symbol (B) on the board explodes, affecting nearby cells.
        Explosion clears symbols and boosts grid multipliers in the radius.
        """
        if bomb_positions is None:
            bomb_positions = self.special_syms_on_board.get("bomb", [])
        
        if not bomb_positions:
            return
        
        all_affected = []
        
        for bomb_pos in bomb_positions:
            bomb_reel = bomb_pos["reel"]
            bomb_row = bomb_pos["row"]
            # Variable radius: 50% small (1), 35% medium, 15% large
            # Features should sometimes feel like duds
            roll = random.random()
            if roll < 0.5:
                radius = 1  # Small explosion - often feels weak
            elif roll < 0.85:
                radius = self.config.bomb_explosion_radius
            else:
                radius = self.config.bomb_explosion_radius + 1
            
            affected_positions = []
            
            # Find all positions within explosion radius
            for reel in range(self.config.num_reels):
                for row in range(self.config.num_rows[reel]):
                    # Calculate Manhattan distance
                    distance = abs(reel - bomb_reel) + abs(row - bomb_row)
                    if distance <= radius:
                        affected_positions.append({"reel": reel, "row": row})
                        
                        # Mark symbol for explosion (will be removed during tumble)
                        self.board[reel][row].explode = True
                        
                        # Double the grid multiplier at this position (same as winning clusters)
                        self.position_multipliers[reel][row] *= 2
                        self.position_multipliers[reel][row] = min(
                            self.position_multipliers[reel][row], 
                            self.config.maximum_board_mult
                        )
            
            # Emit event for this bomb
            elixir_bomb_event(self, bomb_pos, affected_positions)
            all_affected.extend(affected_positions)
        
        # Clear bomb tracking
        self.special_syms_on_board["bomb"] = []
        
        # Update grid multiplier display
        update_grid_mult_event(self)
    
    def apply_symbol_transform(self, transform_positions=None):
        """
        Symbol Transform Feature (Symbol-Based):
        Each Transform symbol (T) transforms ALL instances of one random symbol
        into a high-pay symbol. The transform symbol itself is then removed.
        """
        if transform_positions is None:
            transform_positions = self.special_syms_on_board.get("transform", [])
        
        if not transform_positions:
            return
        
        for transform_pos in transform_positions:
            # Find all symbol types currently on the board
            symbols_on_board = {}
            for reel in range(self.config.num_reels):
                for row in range(self.config.num_rows[reel]):
                    sym_name = self.board[reel][row].name
                    if sym_name in self.config.transformable_symbols:
                        if sym_name not in symbols_on_board:
                            symbols_on_board[sym_name] = []
                        symbols_on_board[sym_name].append((reel, row))
            
            if not symbols_on_board:
                continue
            
            # Select random source symbol to transform
            source_symbol = random.choice(list(symbols_on_board.keys()))
            
            # Select target symbol - 50% chance of "weak" transform to lower tier
            # Features should sometimes feel like duds
            available_targets = [s for s in self.config.transform_target_symbols if s != source_symbol]
            if not available_targets:
                continue
            
            if random.random() < 0.5:
                # Weak transform - pick from lower value targets (H3, H4)
                weak_targets = [s for s in available_targets if s in ['H3', 'H4']]
                if weak_targets:
                    target_symbol = random.choice(weak_targets)
                else:
                    target_symbol = random.choice(available_targets)
            else:
                # Strong transform - prefer H1, H2 (50% of the time)
                strong_targets = [s for s in available_targets if s in ['H1', 'H2']]
                if strong_targets:
                    target_symbol = random.choice(strong_targets)
                else:
                    target_symbol = random.choice(available_targets)
            
            # Transform all instances
            transformed_positions = []
            for reel, row in symbols_on_board[source_symbol]:
                self.board[reel][row] = self.create_symbol(target_symbol)
                transformed_positions.append({"reel": reel, "row": row})
            
            # Emit event for frontend
            if transformed_positions:
                symbol_transform_event(self, source_symbol, target_symbol, transformed_positions)
            
            # Mark the transform symbol for removal
            self.board[transform_pos["reel"]][transform_pos["row"]].explode = True
        
        # Clear transform tracking
        self.special_syms_on_board["transform"] = []

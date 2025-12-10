import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode

class GameConfig(Config):
    """Game specific configuration class for Guillotine (5x4 lines)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "0_0_guillotine"
        self.provider_number = 0
        self.working_name = "Guillotine"
        self.wincap = 5000
        self.win_type = "lines"
        self.rtp = 0.97
        self.include_padding = False  # Not used for lines
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 5
        self.num_rows = [4] * self.num_reels  # 5x4 grid

        # Paytable (Added L5; G is special only)
        # CHANGED: (4, "L5") from 0.25 to 0.3 to satisfy formatting check
        self.paytable = {
            (5, "H1"): 10, (4, "H1"): 5, (3, "H1"): 3,
            (5, "H2"): 8,  (4, "H2"): 4, (3, "H2"): 2,
            (5, "H3"): 5,  (4, "H3"): 2, (3, "H3"): 1,
            (5, "H4"): 3,  (4, "H4"): 1, (3, "H4"): 0.5,
            (5, "H5"): 2,  (4, "H5"): 0.8, (3, "H5"): 0.4,
            (5, "L1"): 2,  (4, "L1"): 0.8, (3, "L1"): 0.4,
            (5, "L2"): 1.5, (4, "L2"): 0.5, (3, "L2"): 0.2,
            (5, "L3"): 1.5, (4, "L3"): 0.5, (3, "L3"): 0.2,
            (5, "L4"): 1,   (4, "L4"): 0.3, (3, "L4"): 0.1,
            (5, "L5"): 1,   (4, "L5"): 0.3, (3, "L5"): 0.1,
            (99, "G"): 0,
        }

        # Paylines (14 lines, 0-indexed rows)
        self.paylines = {
            1:  [0, 0, 0, 0, 0], 2:  [1, 1, 1, 1, 1], 3:  [2, 2, 2, 2, 2],
            4:  [3, 3, 3, 3, 3], 5:  [0, 1, 2, 1, 0], 6:  [3, 2, 1, 2, 3],
            7:  [0, 0, 1, 0, 0], 8:  [3, 3, 2, 3, 3], 9:  [1, 0, 0, 0, 1],
            10: [2, 3, 3, 3, 2], 11: [0, 1, 1, 1, 0], 12: [3, 2, 2, 2, 3],
            13: [1, 2, 3, 2, 1], 14: [2, 1, 0, 1, 2],
        }

        # Special symbols
        self.special_symbols = {
            "wild": ["W"], "scatter": ["S"], "guillotine": ["G"], "multiplier": [],
        }

        # Freespins via scatters
        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 15, 5: 20},
            self.freegame_type: {3: 5, 4: 8, 5: 12},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 2}

        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "FRWCAP": "FRWCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            reel_data = self.read_reels_csv(os.path.join(self.reels_path, f))
            # Remove wilds from Reel 0
            reel_data[0] = [sym for sym in reel_data[0] if sym not in self.special_symbols["wild"]]
            self.reels[r] = reel_data

        # Guillotine feature parameterization
        self.guillotine_config = {
            "jam_drop_weights": {True: 1, False: 1}, # True=Jam, False=Drop
            "base_multiplier": {2: 50, 3: 40, 5: 30, 10: 15, 20: 8, 50: 4, 100: 2, 500: 1},
            "behead_multiplier": {2: 40, 3: 30, 5: 20, 10: 10},
        }

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=False,
                distributions=[
                    Distribution(criteria="basegame", quota=1.0, conditions={"reel_weights": {self.basegame_type: {"BR0": 1}}}),
                ],
            ),
            BetMode(
                name="bonus",
                cost=100.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(criteria="freegame", quota=1.0, conditions={"reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}}}),
                ],
            ),
        ]


import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):

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
        self.wincap = 20000
        self.win_type = "lines"
        # Total RTP target. Mode contribution targets below are normalized to sum to this.
        self.rtp = 0.96
        self.include_padding = False
        self.construct_paths()

        # ---------------------------------------------------------
        # ░█▀█░█░█░█▀█░█▀▀░█░░░█░█░█▀█░▀█▀░█▀█░░░█░░░█▀▀░█░█░█▀█░█▀█
        # ░█▀▀░█░█░█▀▀░█▀▀░█░░░█░█░█░█░░█░░█▀█░░░█░░░█▀▀░█▀█░█▀█░█░█
        # ░▀░░░▀▀▀░▀░░░▀▀▀░▀▀▀░▀▀▀░▀░▀░▀▀▀░▀░▀░░░▀▀▀░▀▀▀░▀░▀░▀░▀░▀▀▀
        #         Reels are NOT modified or sanitized.
        # ---------------------------------------------------------

        self.num_reels = 5
        self.num_rows = [4] * self.num_reels  # 5x4

        # PAYTABLE — unchanged
        self.paytable = {
            (5, "H1"): 10,  (4, "H1"): 5,   (3, "H1"): 3,
            (5, "H2"): 8,   (4, "H2"): 4,   (3, "H2"): 2,
            (5, "H3"): 5,   (4, "H3"): 2,   (3, "H3"): 1,
            (5, "H4"): 3,   (4, "H4"): 1,   (3, "H4"): 0.5,
            (5, "H5"): 2,   (4, "H5"): 0.8, (3, "H5"): 0.4,

            (5, "L1"): 2,   (4, "L1"): 0.8, (3, "L1"): 0.4,
            (5, "L2"): 1.5, (4, "L2"): 0.5, (3, "L2"): 0.2,
            (5, "L3"): 1.5, (4, "L3"): 0.5, (3, "L3"): 0.2,
            (5, "L4"): 1,   (4, "L4"): 0.3, (3, "L4"): 0.1,
            (5, "L5"): 1,   (4, "L5"): 0.3, (3, "L5"): 0.1,

            (99, "G"): 0,
        }

        # PAYLINES (14 lines)
        self.paylines = {
            1:  [0, 0, 0, 0, 0],
            2:  [1, 1, 1, 1, 1],
            3:  [2, 2, 2, 2, 2],
            4:  [3, 3, 3, 3, 3],
            5:  [0, 1, 2, 1, 0],
            6:  [3, 2, 1, 2, 3],
            7:  [0, 0, 1, 0, 0],
            8:  [3, 3, 2, 3, 3],
            9:  [1, 0, 0, 0, 1],
            10: [2, 3, 3, 3, 2],
            11: [0, 1, 1, 1, 0],
            12: [3, 2, 2, 2, 3],
            13: [1, 2, 3, 2, 1],
            14: [2, 1, 0, 1, 2],
        }

        # SPECIAL SYMBOLS (handled at runtime, NOT in reel processing)
        self.special_symbols = {
            "wild": ["W"],
            "scatter": ["S"],
            "guillotine": ["G"],
            "multiplier": [],
        }

        # FREESPINS (unchanged)
        self.freespin_triggers = {
            self.basegame_type: {3: 10, 4: 15, 5: 20},
            self.freegame_type: {3: 5, 4: 8, 5: 12},
        }
        self.anticipation_triggers = {
            self.basegame_type: 2,
            self.freegame_type: 2,
        }

        # ---------------------------------------------------
        # LOAD REELS EXACTLY AS THEY ARE
        # ---------------------------------------------------
        reels_files = {
            "BR0": "BR0.csv",
            "FR0": "FR0.csv",
            "FR4": "FR4.csv",
            "FR5": "FR5.csv",
            "FRWCAP": "FRWCAP.csv",
            # New Overlay Reels
            "SSR_Base": "SSR_Base.csv",
            "SSR_FS3": "SSR_FS3.csv",
            "SSR_FS4": "SSR_FS4.csv",
            "SSR_FS5": "SSR_FS5.csv",
            "SSWCAP": "SSWCAP.csv",
        }
        raw_reels = {}

        for key, filename in reels_files.items():
            reel_data = self.read_reels_csv(os.path.join(self.reels_path, filename))
            raw_reels[key] = reel_data  # ← no modification

        self.reels = raw_reels  # ← THE IMPORTANT PART

        # ---------------------------------------------------
        # GUILLOTINE MULTIPLIER TABLES
        # ---------------------------------------------------
        self.multiplier_set = [2, 3, 4, 5, 10, 15, 20, 25, 50, 100, 200]

        # NERFED WEIGHTS to control RTP
        self.g_mult_weights = {
            2: 500,
            3: 300,
            4: 150,
            5: 50,
            10: 10,
            15: 5,
            20: 2,
            25: 1,
            50: 0.5,
            100: 0.1,
            200: 0.01,
        }

        self.symbol_behead_weights = {
            "H1": {2: 500, 3: 300, 4: 100, 5: 50, 10: 10, 15: 5, 20: 2, 25: 1, 50: 0.1, 100: 0.01, 200: 0.001},
            "H2": {2: 400, 3: 300, 4: 150, 5: 80, 10: 20, 15: 10, 20: 5, 25: 2, 50: 0.5, 100: 0.1, 200: 0.01},
            "H3": {2: 300, 3: 300, 4: 200, 5: 100, 10: 30, 15: 15, 20: 8, 25: 4, 50: 1, 100: 0.2, 200: 0.05},
            "H4": {2: 200, 3: 250, 4: 250, 5: 150, 10: 50, 15: 25, 20: 12, 25: 6, 50: 2, 100: 0.5, 200: 0.1},
            "H5": {2: 100, 3: 200, 4: 250, 5: 200, 10: 80, 15: 40, 20: 20, 25: 10, 50: 4, 100: 1, 200: 0.2},
        }

        self.jam_weights = {"jam": 1, "drop": 9}


        basegame_condition = {
            "reel_weights": {self.basegame_type: {"BR0": 1}},
            "overlay_reels": {self.basegame_type: {"SSR_Base": 1}},
            "force_wincap": False,
            "force_freegame": False,
        }

        fs3_condition = {
            "reel_weights": {
                self.basegame_type: {"BR0": 1},
                self.freegame_type: {"FR0": 1},
            },
            "overlay_reels": {
                self.basegame_type: {"SSR_Base": 1},
                self.freegame_type: {"SSR_FS3": 1},
            },
            "scatter_triggers": {3: 1},
            "force_wincap": False,
            "force_freegame": True,
        }

        fs4_condition = {
            "reel_weights": {
                self.basegame_type: {"BR0": 1},
                self.freegame_type: {"FR4": 1},
            },
            "overlay_reels": {
                self.basegame_type: {"SSR_Base": 1},
                self.freegame_type: {"SSR_FS4": 1},
            },
            "scatter_triggers": {4: 1},
            "force_wincap": False,
            "force_freegame": True,
        }

        fs5_condition = {
            "reel_weights": {
                self.basegame_type: {"BR0": 1},
                self.freegame_type: {"FR5": 1},
            },
            "overlay_reels": {
                self.basegame_type: {"SSR_Base": 1},
                self.freegame_type: {"SSR_FS5": 1},
            },
            "scatter_triggers": {5: 1},
            "force_wincap": False,
            "force_freegame": True,
        }
        # ---------------------------------------------------
        # BONUS MODE SETTINGS (unchanged)
        # ---------------------------------------------------
        self.bonus_modes = {
            "base": {
                "jam_allowed": True,
                "guaranteed_g": False,
                "behead_mode": "ADD",
                "force_g_chance": 0.01,
                "overlay_reels": {
                    self.basegame_type: {"SSR_Base": 1},
                },
            },
            "fs3": {
                "jam_allowed": False,
                "guaranteed_g": False,
                "behead_mode": "ADD",
                "force_g_chance": 0.05,
                "overlay_reels": {
                    self.basegame_type: {"SSR_Base": 1},
                    self.freegame_type: {"SSR_FS3": 1},
                },
            },
            "fs4": {
                "jam_allowed": False,
                "guaranteed_g": True,
                "behead_mode": "ADD",
                "force_g_chance": 0.12,
                "overlay_reels": {
                    self.basegame_type: {"SSR_Base": 1},
                    self.freegame_type: {"SSR_FS4": 1},
                },
            },
            "fs5": {
                "jam_allowed": False,
                "guaranteed_g": True,
                "behead_mode": "MULTIPLY",
                "force_g_chance": 0.20,
                "overlay_reels": {
                    self.basegame_type: {"SSR_Base": 1},
                    self.freegame_type: {"SSR_FS5": 1},
                },
            },
        }

        # ---------------------------------------------------
        # BET MODES (unchanged)
        # ---------------------------------------------------
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                # Contribution targets (normalized): 30/47/13/9 of 96% total
                rtp=0.290909,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=False,
                distributions=[
                    Distribution(criteria="basegame", quota=1.0, conditions=basegame_condition),
                ],
            ),
            BetMode(
                name="fs3",
                cost=100.0,
                rtp=0.455758,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(criteria="freegame", quota=1.0, conditions=fs3_condition),
                ],
            ),
            BetMode(
                name="fs4",
                cost=1376.0,
                rtp=0.126061,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=[
                    Distribution(criteria="freegame", quota=1.0, conditions=fs4_condition),
                ],
            ),
            BetMode(
                name="fs5",
                # FS5 is a rare trigger in natural play; cost is used as the
                # hit-rate scaler when converting per-feature EV to per-spin RTP.
                cost=23200.0,
                rtp=0.087273,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=False,
                distributions=[
                    Distribution(criteria="freegame", quota=1.0, conditions=fs5_condition),
                ],
            ),
        ]
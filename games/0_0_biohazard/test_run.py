
from gamestate import GameState
from game_config import GameConfig

def test_run():
    config = GameConfig()
    gamestate = GameState(config)
    
    print("Running Basegame Spin...")
    gamestate.run_spin(1)
    print("Basegame Spin Complete.")
    
    print("Running Freegame Spin...")
    gamestate.run_freespin()
    print("Freegame Spin Complete.")

if __name__ == "__main__":
    test_run()

from copy import deepcopy

APPLY_TUMBLE_MULTIPLIER = "applyMultiplierToTumble"
UPDATE_GRID = "updateGrid"
WILD_POTION = "wildPotion"
ELIXIR_BOMB = "elixirBomb"
SYMBOL_TRANSFORM = "symbolTransform"


def update_grid_mult_event(gamestate):
    """Pass updated position multipliers after a win."""
    event = {
        "index": len(gamestate.book.events),
        "type": UPDATE_GRID,
        "gridMultipliers": deepcopy(gamestate.position_multipliers),
    }
    gamestate.book.add_event(event)


def wild_potion_event(gamestate, wild_positions):
    """
    Event for Wild Potion feature.
    Emits the positions where wilds were added.
    """
    event = {
        "index": len(gamestate.book.events),
        "type": WILD_POTION,
        "wildsAdded": len(wild_positions),
        "positions": wild_positions,
        "board": [[sym.name for sym in reel] for reel in gamestate.board],
    }
    gamestate.book.add_event(event)


def elixir_bomb_event(gamestate, bomb_position, affected_positions):
    """
    Event for Elixir Bomb feature.
    Emits bomb location, explosion radius, and affected positions.
    """
    event = {
        "index": len(gamestate.book.events),
        "type": ELIXIR_BOMB,
        "bombPosition": bomb_position,
        "affectedPositions": affected_positions,
        "explosionRadius": gamestate.config.bomb_explosion_radius,
        "multiplierBoost": gamestate.config.bomb_multiplier_boost,
        "gridMultipliers": deepcopy(gamestate.position_multipliers),
    }
    gamestate.book.add_event(event)


def symbol_transform_event(gamestate, source_symbol, target_symbol, transformed_positions):
    """
    Event for Symbol Transform feature.
    Emits which symbol was transformed into which, and all affected positions.
    """
    event = {
        "index": len(gamestate.book.events),
        "type": SYMBOL_TRANSFORM,
        "sourceSymbol": source_symbol,
        "targetSymbol": target_symbol,
        "transformedCount": len(transformed_positions),
        "positions": transformed_positions,
        "board": [[sym.name for sym in reel] for reel in gamestate.board],
    }
    gamestate.book.add_event(event)

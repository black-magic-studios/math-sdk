# Multidrop Game

Clusters of 5 or more like-symbols are removed from the board, and symbols above on the reelstrip
fall to fill their place.

#### Basegame:
Tumbling game with Scatter and Wild symbols, featuring grid position multipliers.
Grid positions start in a 'deactivated' state. Once a win occurs at a position,
it is 'activated' starting with a 1x multiplier - for every winning cluster, the multiplier value at that position is increased by +1.
Minimum of 4 Scatter symbols are required for freeSpin triggers.

#### Freegame:
Same as basegame with grid position multipliers that persist and accumulate throughout the freegame.
A minimum of 3 scatters are required for re-triggers.


#### Notes:
Because of the separation between basegame and freegame types - there is an additional freespin entry check to check if the criteria requires a forced 
freespin condition. Otherwise, occurrences of Scatter symbols tumbling onto the board during basegame criteria may appear.
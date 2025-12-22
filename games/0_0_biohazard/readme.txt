# Cluster-based win game

Clusters of 5 or more like-symbols are removed from the board, and symbols above on the reelstrip
fall to fill their place.

#### Basegame:
Grid positions have multipliers. Grid positions start in a 'deactivated' state. Once one win occurs,
the position is 'activated' starting with a 1x multiplier - for every winning cluster, the multiplier value at that position is increased by +1 for every winning position.
Minimum of 4 Scatter symbols are required for freeSpin triggers

#### Freegame:
Same as basegame.
A minimum of 3 scatters are required for re-triggers


#### Notes:
Because of the separation between basegame and freegame types - there is an additional freespin entry check to check of the criteria requires a forced 
freespin condition. Otherwise, occurences of Scatter symbols tumbling onto the board during basegame criteria may appear.
# mandated_vibes

A tool for conforming the vibes of a Spotify playlist based on outliers in the tracks' features (i.e. energy, danceability, valence etc.)

## what do
rename example_keys.json to keys.json, and input your spotify dev keys
from cmd run py mandated_vibes.py [spotify link]
a txt file with a breakdown of the average playlist stats, and the outliers from each statistic will show up for ~~purging~~ removal.

## roadmap
ideally, i'll get it to use some weighted formula to work out which ones really deserve culling, and show them up as due for removal.

the end game is making it so that i can have a lil gui with feature sliders for the current vibe in game, and have the script play spotify songs based on which match the vibe, but for the minute removing songs which are really bad is aight.
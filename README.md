# mandated_vibes

A tool for duplicating and conforming the vibes of a Spotify playlist based on outliers in the tracks' features (i.e. energy, danceability, valence etc.)

## what do
rename example_keys.json to keys.json, and input your spotify dev keys
from cmd run py mandated_vibes.py input
a txt file with a breakdown of the average playlist stats, and the outliers (3 std devs) from each statistic will show up for ~~purging~~ removal, in a new folder in same directory called ```playlist_statistics```.

You'll be prompted if you want to remove the outliers ```y/n```, which will remove all outliers from all playlists passed in.

input can be a txt file with a bunch of playlist links one per line, or a single link.
if the txt file is formatted:
```
Name	url
Name2	url
```
then it will rename the playlist to the name. I use the firefox extension Link Gopher to grab a bunch of links and format as such. 

passing in ```--analyse``` somewhere in the input won't duplicate the playlist to your account, will only write the output files.

## roadmap
ideally, i'll get it to use some weighted formula to work out which ones really deserve culling, and show them up as due for removal. for example, tempo is something that's less connected to vibe than say valence.

~~currently workin towards smth whichll just grab a list of playlists, yoink their tracks and album art, duplicate to my account, and remove songs that aren't matchin the vibe to finetune em a lil more.~~ Done!

~~gonna combine em all so i just mandate vibes from the one script and can choose what i do.~~ Done!

the end game is making it so that i can have a lil gui with feature sliders for the current vibe in game, and have the script play spotify songs based on which match the vibe, but for the minute removing songs which are really bad is aight.

## example output
```
Playlist: Eurovision 2023
no. tracks: 37

Average energy: 0.70 | stdev: 0.15
Average danceability: 0.60 | stdev: 0.12
Average tempo: 126.82 | stdev: 24.56
Average valence: 0.43 | stdev: 0.21
Average acousticness: 0.15 | stdev: 0.22
Average instrumentalness: 0.00 | stdev: 0.00
Average liveness: 0.18 | stdev: 0.11
Average speechiness: 0.07 | stdev: 0.06

Acousticness outliers:
	Bridges (0.84)
	Future Lover (0.89)

Instrumentalness outliers:
	Echo - Eurovision 2023 - Georgia (0.02)

Speechiness outliers:
	Breaking My Heart (0.36)
```
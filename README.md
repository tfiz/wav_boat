# wav_boat
"picture of a wav file that sometimes looks like a boat"

Takes a wav file and an [optional] time interval and generates a picture about the
wav file provided.
One second chunks are mapped to frequency space, added together if the range is
over more than 1 second and split into frequency buckets,
The buckets are normalized and sorted by their relative probability of occurrence.
The output is these buckets plotted over a set frequency range where the color and
amplitude is [red,1 - violet,0] for high to low relative probability.
Left channel is up right channel is down.

And sometimes it looks like a boat.

'''Shell
python wav_boat.py (filename) [start time] [end time]
'''

If no start time specified then a random number is picked and the interval
is one second long.

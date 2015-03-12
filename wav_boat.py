from __future__ import print_function

import sys
import pylab
import random

from scipy.io import wavfile as iowav
from numpy import fft as nf

# offset is starting point in units of samplerates
def get_fft(data, offset, samplerate):
    start = samplerate * offset
    end = start + samplerate
    return nf.rfft(data[start:end])

# A*A_bar
def fft_magnitude(data):
    return pylab.sqrt(data * data.conjugate())

# using greater than 1275 points will result in duplicate colors b/c of integer
#  casting since step size will be less than 1
def color_set(points):
    # 5 transitions with a color range [color_min, color_max]
    # and red being first
    num_transitions = 5.
    color_min = 0.
    color_max = 1.
    color_arr = [[color_max, 0, 0]]

    steps_per_transition = (int)(pylab.floor(points / num_transitions))
    # don't round we will do on-the-fly casting
    step_size = color_max / steps_per_transition

    # to account for non-even divisibility
    steps_per_transition_long = points - 4 * steps_per_transition
    step_size_long = color_max / steps_per_transition_long

    # to avoid wtf we just add each transition explicitly
    # indexing to start at 1 so no repeats

    # red to yellow
    for i in range(1, steps_per_transition + 1):
        color_arr.append([color_max, color_min + i*step_size, color_min])

    # yellow to green
    for i in range(1, steps_per_transition + 1):
        color_arr.append([color_max - i*step_size, color_max, color_min ])

    # green to cyan
    for i in range(1, steps_per_transition + 1):
        color_arr.append([color_min, color_max, color_min + i*step_size])

    # cyan to blue
    for i in range(1, steps_per_transition + 1):
        color_arr.append([color_min, color_max - i*step_size, color_max])

    # blue to violet (extra goes here)
    for i in range(1, steps_per_transition_long + 1):
        color_arr.append([color_min + i*step_size_long, color_min, color_max])

    return color_arr

def rainbow_plot_stereo(left, right, wid, filename):
    pylab.figure()
    pylab.axis('off')
    pylab.hold(True)

    # this is our rainbow coloring
    # red to violet
    colors = color_set(len(left))

    for i in range(len(left)):
        left_val = left[i][0]
        right_val = right[i][0]
        # we plot from 0 up for the left channel and 0 down for the right channel
        # with a quarter-period sine wave scaling
        pylab.plot([left_val, left_val], [0, pylab.sin(left[i][1] * pylab.pi / 2)], lw=wid, color=colors[i])
        pylab.plot([right_val, right_val], [0, -1 * pylab.sin(right[i][1] * pylab.pi / 2)], lw=wid, color=colors[i])

    pylab.hold(False)
    pylab.savefig(filename, bbox_inches='tight', pad_inches=0, transparent=True)

def rainbow_plot_mono(data, wid, filename):
    pylab.figure()
    pylab.axis('off')
    pylab.hold(True)

    # this is our rainbow coloring
    # red to violet
    colors = color_set(len(data))

    for i in range(len(data)):
        val = data[i][0]
        pylab.plot([val, val], [0, 1], lw=wid, color=colors[i])

    pylab.hold(False)
    pylab.savefig(filename, bbox_inches='tight', pad_inches=0, transparent=True)


def process(samplerate, waveform, start_time, end_time):
    # end_time to -1 for (mostly) whole song
    # our bin size
    frqstep = 100
    # can fiddle up a lot of the high frequency data is minimal
    lowfrq = 20
    highfrq = 15000

    # inital....
    len_data = len(waveform)
    # floored number of seconds for integer value
    seconds_in_z = int(pylab.floor(len_data / samplerate))

    print("Working over %d to %d" % (start_time, end_time))
    # per-second ft in range [start_time, end_time - 1]
    for i in range(start_time, end_time if end_time != -1 else seconds_in_z):
        print ("processing second %d" % i)
        # first time? init
        if (i == start_time):
            ft = fft_magnitude(get_fft(waveform, i, samplerate))
            ft = ft.flatten('F')
            left_channel = ft[:samplerate]
            right_channel = ft[samplerate:]
        # otherwise append
        else:
            ft = fft_magnitude(get_fft(waveform, i, samplerate))
            ft = ft.flatten('F')
            left_channel += ft[:samplerate]
            right_channel += ft[samplerate:]

    # and the last bit beyond an integer second
    # neglected for now
    # extra = nf.rfft(waveform[seconds_in_z*samplerate:])
    # mapping_constant = samplerate / len(extra)


    print("finished! organizing")

    # create our bins
    left_channel_bins = [sum(left_channel[i*frqstep:i*(frqstep+1)]) for i in range(int(lowfrq/frqstep), int(highfrq/frqstep))]
    right_channel_bins = [sum(right_channel[i*frqstep:i*(frqstep+1)]) for i in range(int(lowfrq/frqstep), int(highfrq/frqstep))]

    # scale and only take reals even though we only have reals anyways
    # less complaining amount casting and precision loss
    left_channel_bins = pylab.real(left_channel_bins) / pylab.real(max(left_channel_bins))
    right_channel_bins = pylab.real(right_channel_bins) / pylab.real(max(right_channel_bins))

    # setup frequency domain data in ~[0hz, 20000hz] by frestp hertz steps
    frq_dom = [i*frqstep for i in range(len(left_channel_bins))]

    # combine freq and relative occurrence
    left = zip(frq_dom, left_channel_bins)
    right = zip(frq_dom, right_channel_bins)
    # start with highest
    #return left
    left = sorted(left, key=lambda val: val[1], reverse=True)
    right = sorted(right, key=lambda val: val[1], reverse=True)

    return [left, right, start_time, end_time]

def to_file(filename_wav, start_time, end_time):
    print("attempting to open")
    [samplerate, data] = iowav.read(filename_wav)
    print("success! we'll try to process")
    # random second interval if start_time is -1
    if (start_time == -1):
        start_time = random.randint(0, pylab.floor(len(data) / samplerate))
        end_time = start_time + 1
    elif (end_time > len(data) / samplerate):
        print("end_time too long, truncating")
        end_time = -1

    [l, r, s, e] = process(samplerate, data, start_time, end_time)
    # plot it. 2 or 3 seems to be a good line width)
    filename_out = "%s_%d-%d.png" % (filename_wav, s, e)
    print("plotting and saving to %s" % filename_out)
    rainbow_plot_stereo(l, r, 3, filename_out)

def main():
    if (not sys.argv[1]):
        print("usage: python wave_chunk.py (filename) [start time] [end time]")
        return

    s = -1
    e = -1
    if (len(sys.argv) > 2):
        s = int(sys.argv[2])
        e = s + 1
        if (len(sys.argv) > 3):
            e = int(sys.argv[3])

    to_file(sys.argv[1], s, e)

if __name__ == '__main__':
    main()

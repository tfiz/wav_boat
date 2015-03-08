from __future__ import print_function

import numpy as np
import sys
import scipy.io.wavfile
import pylab

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


def process(samplerate, waveform, filename):
    # our bin size
    frqstep = 100
    # can fiddle up a lot of the high frequency data is minimal
    lowfrq = 20
    highfrq = 15000
    start_time = 0
    # end_time to -1 for (mostly) whole song
    end_time = 5

    # inital....
    ft_len = None
    len_data = len(waveform)
    # floored number of seconds for integer value
    seconds_in_z = int(pylab.floor(len_data / samplerate))

    # per-second ft in range [start_time, end_time - 1]
    for i in range(start_time, end_time if end_time != -1 else seconds_in_z):
        print ("processing second %d" % i)
        # first time? init
        if (not i):
            print("hahah")
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
    extra = nf.rfft(waveform[seconds_in_z*samplerate:])
    mapping_constant = samplerate / len(extra)




    print("finished! organizing")

    # create our bins
    left_channel_bins = [sum(left_channel[i*frqstep:i*(frqstep+1)]) for i in range(int(lowfrq/frqstep), int(highfrq/frqstep))]
    right_channel_bins = [sum(right_channel[i*frqstep:i*(frqstep+1)]) for i in range(int(lowfrq/frqstep), int(highfrq/frqstep))]

    # scale
    left_channel_bins = pylab.real(left_channel_bins) / max(left_channel_bins)
    right_channel_bins = pylab.real(right_channel_bins) / max(right_channel_bins)

    # setup frequency domain data in ~[0hz, 20000hz] by frestp hertz steps
    frq_dom = [i*frqstep for i in range(len(left_channel_bins))]

    # combine freq and relative occurrence
    left = zip(frq_dom, left_channel_bins)
    right = zip(frq_dom, right_channel_bins)
    # start with highest
    #return left
    left = sorted(left, key=lambda val: val[1], reverse=True)
    right = sorted(right, key=lambda val: val[1], reverse=True)

    # plot it. 2 or 3 seems to be a good line width)
    filename = "%s.png" % filename
    print("plotting and saving to %s" % filename)
    rainbow_plot_stereo(left, right, 3, filename)

def main():
    if (not sys.argv[1]):
        print("usage: python color.py [filename]")
        return
    print("attempting to open")
    [samplerate, data] = scipy.io.wavfile.read(sys.argv[1])
    print("success! we'll try to process")
    process(samplerate, data, sys.argv[1])

if __name__ == '__main__':
    main()

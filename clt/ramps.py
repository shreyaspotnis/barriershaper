import numpy as np
from random import random
from scipy.interpolate import interp1d


def square(n_bins):
    return [100] * (n_bins / 2) + [0] * (n_bins - n_bins/2)


def triangle(n_bins):
    val = range(n_bins)
    for i in range(n_bins):
        if i < n_bins / 2:
            val[i] = i * 100 / (n_bins / 2)
        else:
            val[i] = (n_bins - i) * 100 / (n_bins / 2)
    return val


def rand(n_bins):
    return [int(random() * 100) for _ in range(n_bins)]

def fiftypercent(n_bins):
    return [50] * n_bins

def make_full_ramp(short_ramp, n_full, minValue=0, maxValue=100,
                   interpolation='nearest'):
    n_bins = len(short_ramp)
    i_bin = n_full / n_bins
    addresses = np.arange(n_full)
    values = np.zeros(n_full)

    short_val_np = np.zeros(len(short_ramp) + 1, dtype=float)
    short_val_np[:-1] = np.array(short_ramp)
    short_val_np[-1] = short_val_np[0]

    short_addr_np = np.arange(n_bins + 1, dtype=float) * i_bin
    interpolator = interp1d(short_addr_np, short_val_np,  kind=interpolation)

    values = interpolator(addresses)
    values *= (maxValue - minValue) / 100.0
    values += minValue

    values = np.array(values, dtype=int)

    #     print(values.dtype)
    # else:
    #     for i in range(n_bins):
    #         curr_val = float(short_ramp[i])*(maxValue - minValue) / 100.0
    #         values[i*i_bin:(i+1)*i_bin] = int(curr_val) + minValue

    return (addresses, values)


ramp_dict = {'square': square, 'triangle': triangle, 'rand': rand, 'fiftypercent': fiftypercent}
interp_types = ['linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic']
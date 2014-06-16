import numpy as np
from random import random


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

ramp_dict = {'square': square, 'triangle': triangle, 'rand': rand}

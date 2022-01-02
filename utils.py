import numpy as np

def rotate_list(l, n):
    return l[-n:] + l[:-n]
from collections import defaultdict
from itertools import chain, islice
import json
import struct


def islice_from(it, start):
    return islice(it, start, len(it))


def full_circle(it, start):
    return chain(islice_from(it, start), islice(it, start))


def log_byte(b):
    return '{:02x}'.format(b)


def log_short(s):
    p = struct.pack('<H', s)
    return ''.join('{:02x}'.format(b) for b in p)


def log_int(i):
    p = struct.pack('<I', i)
    return ''.join('{:02x}'.format(b) for b in p)
    
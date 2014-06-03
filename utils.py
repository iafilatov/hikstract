from itertools import chain, islice
import struct


def islice_from(it, start):
    '''Given a sequence 0..start..N, iterate over start..N'''
    return islice(it, start, len(it))


def full_circle(it, start):
    '''Given a sequence 0..start..N, iterate over start..N,
    then over 0..start
    '''
    return chain(islice_from(it, start), islice(it, start))


def log_short(s):
    '''Return a string representation of s as little-endian unsigned short'''
    p = struct.pack('<H', s)
    return ''.join('{:02x}'.format(b) for b in p)


def log_int(i):
    '''Return a string representation of i as little-endian unsigned int'''
    p = struct.pack('<I', i)
    return ''.join('{:02x}'.format(b) for b in p)

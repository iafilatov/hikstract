import logging
import os
import subprocess as sp

from config import config
import utils as u


logger = logging.getLogger(__name__)


def extract(vrec):
    start_dt = vrec.start_dt
    start_dt_str = start_dt.strftime('%Y-%m-%d_%H:%M:%S')
    out_dir = os.path.join(config['main']['output_dir'],
                           '{:04d}'.format(start_dt.year),
                           '{:02d}'.format(start_dt.month),
                           '{:02d}'.format(start_dt.day))
    try:
        os.makedirs(out_dir, mode=0o750)
    except FileExistsError:
        pass

    in_fpath = os.path.join(os.path.dirname(vrec._h_idx_file.name),
                            'hiv{:05d}.mp4'.format(vrec.section.idx))

    # Extract video stream

    logger.info('Extracting video record from ' + start_dt_str)
    logger.debug('Reading from {}, start {}, end {}'
                 .format(in_fpath,
                         u.log_int(vrec.start_offset),
                         u.log_int(vrec.start_offset + vrec.length)))

    converter = config['main']['converter']

    out_fmt = config['main']['output_format'] if converter else 'mp4'
    out_fname = 'rec_{}.{}'.format(start_dt_str, out_fmt)
    out_fpath = os.path.join(out_dir, out_fname)

    # We want FileExistsError propagated
    open(out_fpath, 'x')

    if converter:
        cmd = [converter, '-i', '-']
        cmd.extend(config['advanced']['converter_args'].split())
        cmd.append(out_fpath)

        logger.debug('Starting converter: {}'.format(' '.join(cmd)))

        def dest_open():
            # open(out_fpath, 'x') has left a 0-length file which the converter
            # will likely refuse to clobber, so it should be deleted
            os.remove(out_fpath)

            p = sp.Popen(cmd, stdin=sp.PIPE)
            p.write = p.stdin.write
            return p

    else:
        logger.debug('Saving original stream to {}'.format(out_fpath))

        def dest_open():
            return open(out_fpath, 'wb')

    with open(in_fpath, 'rb') as inpt, dest_open() as outpt:
        inpt.seek(vrec.start_offset)
        left = vrec.length
        while left > 0:
            buf = inpt.read(max(1024 * 1024, left))
            left -= len(buf)
            outpt.write(buf)

    # Create a snapshot
    snap_fmt = config['main']['snapshot_format']
    if snap_fmt:
        fname_snap = 'snap_{}.{}'.format(start_dt_str, snap_fmt)
        out_fpath_snap = os.path.join(out_dir, fname_snap)
        ss = vrec.duration * config.getfloat('advanced', 'snapshot_pos')

        cmd = [converter, '-ss', str(ss), '-i', out_fpath]
        cmd.extend(config['advanced']['converter_args_snap'].split())
        cmd.append(out_fpath_snap)

        logger.info('Extracting snapshot from {}'.format(out_fpath_snap))
        logger.debug('Starting converter: {}'.format(' '.join(cmd)))

        sp.Popen(cmd).wait()

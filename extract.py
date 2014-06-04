from contextlib import closing
import logging
import os
import subprocess as sp

from config import cfg
import utils as u


LOG = logging.getLogger(__name__)


def extract(vrec):
    start_dt = vrec.start_dt
    start_dt_str = start_dt.strftime('%Y-%m-%d_%H:%M:%S')
    out_dir = os.path.join(cfg['main']['output_dir'],
                           '{:04d}'.format(start_dt.year),
                           '{:02d}'.format(start_dt.month),
                           '{:02d}'.format(start_dt.day))
    try:
        os.makedirs(out_dir, mode=0o750)
    except FileExistsError:
        pass
    out_fpath = os.path.join(out_dir, 'rec_{}.mp4'.format(start_dt_str))
    # We want FileExistsError propagated
    open(out_fpath, 'x')

    in_fpath = os.path.join(os.path.dirname(vrec.h_idx_file.name),
                            'hiv{:05d}.mp4'.format(vrec.section.idx))
    cmd = ['avconv', '-i', '-']
    cmd.extend(cfg['advanced']['avconv_args'].split())
    cmd.append(out_fpath)
    
    # Extract video stream

    LOG.info('Extracting video record from ' + start_dt_str)
    LOG.debug('Reading from {}, start {}, end {}'
              .format(in_fpath, u.log_int(vrec.start_offset),
                      u.log_int(vrec.start_offset + vrec.length)))

    converter = cfg['main']['converter']
    if converter:
        cmd = [converter, '-i', '-']
        cmd.extend(cfg['advanced'][converter + '_args'].split())
        cmd.append(out_fpath)

        LOG.debug('Starting converter: {}'.format(' '.join(cmd)))

        def dest_open():
            p = sp.Popen(cmd, stdin=sp.PIPE)
            p.write = p.stdin.write
            return p
    else:
        LOG.debug('Saving original stream to {}'.format(out_fpath))

        def dest_open():
            return open(out_fpath, 'wb')

    with open(in_fpath, 'rb') as inpt, dest_open() as outpt:
        inpt.seek(vrec.start_offset)
        left = vrec.length
        while left > 0:
            buf = inpt.read(max(1024*1024, left))
            left -= len(buf)
            outpt.write(buf)

    # Create a snapshot
    snap_fmt = cfg['main']['snapshot_format']
    if snap_fmt:
        out_fpath_snap = os.path.join(out_dir, 'snap_{}.{}'
                                               .format(start_dt_str, snap_fmt))
        ss = vrec.duration * cfg.getfloat('advanced', 'snapshot_pos')

        cmd = [converter, '-ss', str(ss), '-i', out_fpath]
        cmd.extend(cfg['advanced'][converter + '_args_snap'].split())
        cmd.append(out_fpath_snap)
        
        LOG.info('Extracting snapshot from {}'.format(out_fpath_snap))
        LOG.debug('Starting converter: {}'.format(' '.join(cmd)))
        
        sp.Popen(cmd).wait()

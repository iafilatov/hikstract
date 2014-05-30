import logging
import os
import subprocess as sp

from config import cfg
import utils as u

LOG = logging.getLogger(__name__)

def extract(video_record):
    start_dt = video_record.start_dt
    out_dir = os.path.join(cfg['main']['output_dir'],
                           '{:04d}'.format(start_dt.year),
                           '{:02d}'.format(start_dt.month),
                           '{:02d}'.format(start_dt.day))
    try:
        os.makedirs(out_dir, mode=0o750)
    except FileExistsError:
        pass
    out_fpath = os.path.join(out_dir,
                             'rec_{:%Y-%m-%d_%H:%M:%S}.mp4'.format(start_dt))
    # We want FileExistsError propagated
    open(out_fpath, 'x')
    
    h_idx_file = video_record.section.h_idx_file
    in_fpath = os.path.join(os.path.dirname(h_idx_file.name),
                            'hiv{:05d}.mp4'.format(video_record.section.idx))
    cmd = ['avconv', '-i', '-']
    cmd.extend(cfg['advanced']['avconv_args'].split())
    cmd.append(out_fpath)
    
    LOG.info('Extracting video record from'
             ' {:%Y-%m-%d_%H:%M:%S}'.format(start_dt))
    LOG.debug('Reading from {}, start {}, end {}'\
              .format(in_fpath, u.log_int(video_record.start_offset),
                    u.log_int(video_record.start_offset + video_record.length)))
    LOG.debug('Starting converter: {}'.format(' '.join(cmd)))
    
    with open(in_fpath, 'rb') as f, sp.Popen(cmd, stdin=sp.PIPE) as p:
        f.seek(video_record.start_offset)
        left = video_record.length
        while left > 0:
            buf = f.read(max(1024*1024, left))
            left -= len(buf)
            p.stdin.write(buf)
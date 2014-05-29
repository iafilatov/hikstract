import os
import subprocess as sp

from config import cfg


def extract(datadir, section, video_record):
    dt_start = video_record.datetime_start
    out_dir = os.path.join((cfg['main']['output_dir'],
                            '{:04d}'.format(dt_start.year),
                            '{:04d}'.format(dt_start.month),
                            '{:04d}'.format(dt_start.day)))
    try:
        os.makedirs(out_dir, mode=0o750)
    except FileExistsError:
        pass
    out_fpath = os.path.join(out_dir,
                             'rec_{:%Y-%m-%d_%H:%M:%S}.mp4'.format(dt_start))
    # We want FileExistsError propagated
    open(out_fpath, 'x')
    
    in_fpath = os.path.join((cfg['main']['data_dir'],
                             datadir,
                             'hiv{:05d}.mp4'.format(section.idx)))
    cmd = ['avconv', '-i', '-', '-c:v', 'copy', out_fpath]
    with open(in_fpath, 'rb') as f, sp.Popen(cmd, stdin=sp.PIPE) as p:
        f.seek(video_record.start_offset)
        left = video_record.length
        while left > 0:
            buf = f.read(max(1024*1024, left))
            left -= len(buf)
            p.stdin.write(buf)
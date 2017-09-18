import logging
import os

from shutil import copyfile
from tempfile import NamedTemporaryFile


from config import config
from transcode import transcode
from utils import log_int


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
    converter = config['main']['converter']
    out_fmt = config['main']['output_format'] if converter else 'mp4'
    out_fname = 'rec_{}.{}'.format(start_dt_str, out_fmt)
    out_fpath = os.path.join(out_dir, out_fname)

    # We want FileExistsError propagated
    open(out_fpath, 'x')

    # open(out_fpath, 'x') has left a 0-length file which the converter
    # will likely refuse to clobber, so it should be deleted
    os.remove(out_fpath)

    # Create a temp file with just the portion of the stream we need
    with NamedTemporaryFile() as temp:
        with open(in_fpath, 'rb') as inpt:
            inpt.seek(vrec.start_offset)
            left = vrec.length
            while left > 0:
                buf = inpt.read(max(16 * 1024, left))
                left -= len(buf)
                temp.write(buf)

        temp.flush()
        temp_fpath = temp.name

        if config.getboolean('main', 'analyze_motion'):
            from motion import has_motion
            if not has_motion(temp_fpath):
                logger.info('No motion detected in {}, skipping'
                            .format(temp_fpath))
                return

        logger.info('Extracting video record from ' + start_dt_str)
        logger.debug('Reading from {}, start {}, end {}'
                     .format(in_fpath,
                             log_int(vrec.start_offset),
                             log_int(vrec.start_offset + vrec.length)))

        if converter:
            xcoder_args = config['advanced']['converter_args'].split()
            transcode(temp_fpath, out_fpath,
                      converter=converter,
                      additional_flags=xcoder_args)
        else:
            logger.debug('Saving original stream to {}'.format(out_fpath))
            copyfile(temp_fpath, out_fpath)

    # Create a snapshot
    snap_fmt = config['main']['snapshot_format']
    if snap_fmt:
        fname_snap = 'snap_{}.{}'.format(start_dt_str, snap_fmt)
        out_fpath_snap = os.path.join(out_dir, fname_snap)
        ss = vrec.duration * config.getfloat('advanced', 'snapshot_pos')

        logger.info('Extracting snapshot from {}'.format(out_fpath))

        xcoder_args = config['advanced']['converter_args_snap'].split()
        xcoder_args += ['-ss', str(ss)]
        transcode(out_fpath, out_fpath_snap,
                  converter=converter,
                  additional_flags=xcoder_args)

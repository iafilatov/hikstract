import logging

from contextlib import contextmanager
from subprocess import PIPE, Popen


logger = logging.getLogger(__name__)


@contextmanager
def run_transcoder(input, output, converter='ffmpeg', additional_flags=None):
    cmd_in, proc_in = _get_io_args(input)
    cmd_out, proc_out = _get_io_args(output)

    cmd = [converter, '-i', cmd_in] + (additional_flags or []) + [cmd_out]
    logger.debug('Starting converter: {}'.format(' '.join(cmd)))

    with Popen(cmd, stdin=proc_in, stdout=proc_out) as xcoder:
        # Give it file-like read and write methods.
        if xcoder.stdin:
            xcoder.write = xcoder.stdin.write
        if xcoder.stderr:
            xcoder.read = xcoder.stderr.read
        yield xcoder


def _get_io_args(obj):
    if obj == '-':
        # Caller will handle reading/writing.
        return '-', PIPE
    if isinstance(obj, str):
        # A file path - converter will handle it.
        return obj, None
    # Assuming a file-like object, we'll will pipe to/from it.
    return '-', obj

from datetime import datetime as dt
import logging
import struct

import utils as u


logger = logging.getLogger(__name__)
EPOCH = dt.utcfromtimestamp(0)


class IndexFile:

    def __init__(self, path):
        self.f = open(path, 'rb')
        self._header = None
        self._sections = None

    @property
    def header(self):
        if self._header is None:
            self._header = Header.make(self)
        return self._header

    @property
    def sections(self):
        if self._sections is None:
            self._sections = []
            if self.header.total_sec > 1:
                for idx in range(self.header.cur_sec_idx):
                    sec = Section.make(self, idx)
                    self._sections.append(sec)
            if self.header.total_sec >= 1:
                cur_sec = CurrentSection.make(self)
                self.sections.append(cur_sec)
        return self._sections

    def __getattr__(self, attr):
        return getattr(self.f, attr)

    def __del__(self):
        self.close()


class Item:
    def __init__(self, h_idx_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h_idx_file = h_idx_file

    @classmethod
    def make(cls, f, idx=0, start=None):
        if start is None:
            start = cls.start
        pos = start + idx * cls.size
        f.seek(pos)
        logger.debug('Making {} at {}:{:x}'.format(cls.__name__, f.name, pos))
        buf = f.read(cls.size)
        fields = struct.unpack(cls.fmt, buf)
        item = cls(f, *fields)
        item._pos = pos
        logger.debug(u.log_item_fields(item))
        return item


class Header(Item):
    fmt = '<H 10x B 3x B 3x B 3x'
    start = 0
    size = 24
    max_items = 1

    def __init__(self, h_idx_file, revision, rec_sec_num, total_sec,
                 cur_sec_idx, *args, **kwargs):
        super().__init__(h_idx_file, *args, **kwargs)
        self.revision = revision
        self.rec_sec_num = rec_sec_num
        self.total_sec = total_sec
        self.cur_sec_idx = cur_sec_idx


class Section(Item):
    fmt = '<B 5x B x I I 16x'
    start = 0x500
    size = 32
    max_items = 149

    def __init__(self, h_idx_file, idx, last_vrec_idx, start_ts, end_ts,
                 *args, **kwargs):
        super().__init__(h_idx_file, *args, **kwargs)
        self.idx = idx
        self.last_vrec_idx = last_vrec_idx
        self.start_dt = dt.utcfromtimestamp(start_ts)
        self.end_dt = dt.utcfromtimestamp(end_ts)
        self._video_records = None

    @property
    def video_records(self):
        if self._video_records is None:
            self._video_records = []
            rec_sec_num = self._h_idx_file.header.rec_sec_num
            vrecs_start = Section.start + Section.size * rec_sec_num
            for idx in range(self.last_vrec_idx + 1):
                start = (vrecs_start
                         + VideoRecord.max_items * VideoRecord.size * self.idx)
                vrec = VideoRecord.make(self._h_idx_file, idx, start)
                vrec.section = self
                self._video_records.append(vrec)
        return self._video_records


class CurrentSection(Section):
    fmt = '<B x B x I I 4x'
    start = 0x30
    size = 16
    max_items = 1


class Record(Item):
    def __init__(self, h_idx_file, start_offset, end_offset, *args, **kwargs):
        super().__init__(h_idx_file, *args, **kwargs)
        self.start_offset = start_offset
        self.length = end_offset - start_offset


class VideoRecord(Record):
    fmt = '8x I 4x I 20x I I 32x'
    start = 0x17a0
    size = 80
    max_items = 256

    def __init__(self, h_idx_file, start_dt, end_dt,
                 *args, **kwargs):
        super().__init__(h_idx_file, *args, **kwargs)
        self.start_dt = dt.utcfromtimestamp(start_dt)
        self.end_dt = dt.utcfromtimestamp(end_dt)
        self.duration = (self.end_dt - self.start_dt).seconds

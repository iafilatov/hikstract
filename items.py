from datetime import datetime as dt
import logging
import struct

import utils as u


LOG = logging.getLogger(__name__)
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
            cur_sec = CurrentSection.make(self)
            cur_idx = cur_sec.idx
            # CurrentSection has ffff in idx field in vanilla index
            if cur_idx != 0xffff:
                for idx in range(cur_idx):
                    sec = Section.make(self, idx)
                    self._sections.append(sec)
                self.sections.append(cur_sec)
        return self._sections
    
    def __getattr__(self, attr):
        return getattr(self.f, attr)
    
    def __del__(self):
        self.close()
            

class Item:
    def __init__(self, h_idx_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.h_idx_file = h_idx_file
    
    @classmethod
    def make(cls, f, idx=0, start=None):
        if start is None:
            start = cls.start
        f.seek(start + idx*cls.size)
        LOG.debug('Making {} at {}:{:x}'.format(cls.__name__,
                                                f.name,
                                                f.tell()))
        buf = f.read(cls.size)
        fields = struct.unpack(cls.fmt, buf)
        return cls(f, *fields)
    

class Header(Item):
    fmt = '<H 14x'
    start = 0
    size = 16
    max_items = 1

    def __init__(self, h_idx_file, revision, *args, **kwargs):
        super().__init__(h_idx_file, *args, **kwargs)
        self.revision = revision
        
        
class Section(Item):
    fmt = '<H 6x I I 16x'
    start = 0x500
    size = 32
    max_items = 149

    def __init__(self, h_idx_file, idx, start_ts, end_ts,
                 *args, **kwargs):
        super().__init__(h_idx_file, *args, **kwargs)
        self.idx = idx
        self.start_dt = dt.utcfromtimestamp(start_ts)
        self.end_dt = dt.utcfromtimestamp(end_ts)
        self._video_records = None
        
    @property
    def video_records(self):
        if self._video_records is None:
            self._video_records = []
            for idx in range(VideoRecord.max_items):
                start = VideoRecord.start\
                        + VideoRecord.max_items * VideoRecord.size * self.idx
                vrec = VideoRecord.make(self.h_idx_file, idx, start)
                if vrec.end_dt == EPOCH:
                    # Record either in progress or not initialized
                    break
                self._video_records.append(vrec)
        return self._video_records
        
        
class CurrentSection(Section):
    fmt = '<H 2x I I 4x'
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
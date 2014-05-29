from datetime import datetime, timezone, _EPOCH
import struct


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
    @classmethod
    def make(cls, f, idx=0):
        f.seek(cls.start + idx*cls.size)
        buf = f.read(cls.size)
        fields = struct.unpack(cls.fmt, buf)
        return cls(*fields)
    

class Header(Item):
    fmt = '<H 14x'
    start = 0
    size = 16
    max_items = 1

    def __init__(self, revision, *args, **kwargs):
        self.revision = revision
        super().__init__(*args, **kwargs)
        
        
class Section(Item):
    fmt = '<H 6x <I <I 16x'
    start = 0x500
    size = 32
    max_items = 149

    def __init__(self, idx, start_datetime, end_datetime):
        self.idx = idx
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self._video_records = None
        
    @property
    def video_records(self):
        if self._video_records is None:
            self._video_records = []
            for idx in range(VideoRecord.max_items):
                vrec = VideoRecord.make(self, idx)
                if vrec.end_time == _EPOCH:
                    # Record either in progress or not initialized
                    break
                self._video_records.append(vrec)
        return self._video_records
        
        
class CurrentSection(Section):
    fmt = '<H 2x <I <I 4x'
    start = 0x30
    size = 16
    max_items = 1
        

class Record(Item):
    def __init__(self, start_offset, length, *args, **kwargs):
        self.start_offset = start_offset
        self.length = length
        super().__init__(*args, **kwargs)
        
        
class VideoRecord(Record):
    fmt = '8x <I 4x <I 20x <I <I 32x'
    start = 0x17a0
    size = 80
    max_items = 256

    def __init__(self, start_datetime, end_datetime, *args, **kwargs):
        self.start_datetime = self.parse_timestamp(start_datetime)
        self.end_datetime = self.parse_timestamp(end_datetime)
        super().__init__(*args, **kwargs)
        
    @classmethod
    def parse_timestamp(cls, timestamp):
        return datetime.fromtimestamp(timestamp, timezone.utc)
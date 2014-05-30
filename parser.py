from collections import defaultdict
import json
import logging
import os

from config import cfg
from extract import extract
import items
import utils as u


LOG = logging.getLogger(__name__)


class Parser():
    _dbfile = cfg['advanced']['db_file']
    
    def __init__(self):
        self.read_db()
        
    def update(self):
        try:
            self._do_update()
        except FileExistsError as e:
            LOG.info('File {} exists, will not proceed'.format(e.filename))
        
    def _do_update(self):
        for datadir in os.listdir(cfg['main']['data_dir']):
            if not datadir.startswith('datadir'):
                continue
            
            LOG.debug('Entering {}'.format(datadir))
            
            h_idx_path = os.path.join(cfg['main']['data_dir'],
                                      datadir,
                                      cfg['advanced']['h_index_file'])
            idx_file = items.IndexFile(h_idx_path)

            # Skip if revision has not changed
            db_dir_entry = self._db['datadirs'][datadir]
            if db_dir_entry['revision'] == idx_file.header.revision:
                continue
            
            cur_sec_idx = db_dir_entry['cur_section']
            for sec in u.full_circle(idx_file.sections, cur_sec_idx):
                
                LOG.debug('Entering section {}'.format(sec.idx))
                               
                if sec.idx == cur_sec_idx:
                    next_vrec_idx = db_dir_entry['last_vrec'] + 1
                else:
                    next_vrec_idx = 0
                db_dir_entry['cur_section'] = sec.idx
                self.save_db()
                for vrec in u.islice_from(sec.video_records, next_vrec_idx):
                    extract(datadir, sec, vrec)
                    db_dir_entry['last_vrec'] = next_vrec_idx
                    self.save_db()
                    
    def read_db(self):
        self._db = {'datadirs': defaultdict(lambda: {
                                                     'revision': 0,
                                                     'cur_section': 0,
                                                     'last_vrec': -1,
                                                     })}
        try:
            with open(self._dbfile, 'r') as f:
                db_data = json.load(f)
            self._db.update(db_data)
        except FileNotFoundError:
            pass
        
    def save_db(self):
        with open(self._dbfile, 'w') as f:
            json.dump(self._db, f)
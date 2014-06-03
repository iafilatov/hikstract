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
    data_root = cfg['main']['data_dir']
    h_index_fname = cfg['advanced']['h_index_file']

    def __init__(self):
        self._db = self._read_db()

    def update(self):
        get_idx = lambda dname: int(dname[7:])

        listing = sorted((fn for fn in os.listdir(self.data_root)
                          if fn.startswith('datadir')),
                         key=get_idx)
        cur_datadir_idx = get_idx(self._db['cur_datadir'])

        for datadir in u.full_circle(listing, cur_datadir_idx):
            self.update_datadir(datadir)

    def update_datadir(self, datadir):
        LOG.info('Entering {}'.format(datadir))

        h_idx_file = items.IndexFile(os.path.join(self.data_root,
                                                  datadir,
                                                  self.h_index_fname))
        h_idx_file_rev = h_idx_file.header.revision

        LOG.info('Index revision is {}'.format(h_idx_file_rev))

        db_dir_entry = self._db['datadirs'][datadir]

        # Skip if revision has not changed
        if db_dir_entry['revision'] == h_idx_file_rev:
            LOG.info('Revision unchanged, nothing to update')
            return

        cur_sec_idx = db_dir_entry['cur_section']
        for sec in u.full_circle(h_idx_file.sections, cur_sec_idx):

            LOG.debug('Entering section {}'.format(sec.idx))

            if sec.idx == cur_sec_idx:
                next_vrec_idx = db_dir_entry['last_vrec'] + 1
            else:
                next_vrec_idx = 0

            next_vrecs = u.islice_from(sec.video_records, next_vrec_idx)
            for i, vrec in enumerate(next_vrecs):
                try:
                    extract(vrec)
                    db_dir_entry['last_vrec'] = next_vrec_idx + i
                    db_dir_entry['cur_section'] = sec.idx
                    self._db['cur_datadir'] = datadir
                    self._save_db()
                except FileExistsError as e:
                    LOG.info('File {} exists, will not overwrite'
                              .format(e.filename))

        LOG.info('Done processing revision {}'
                 .format(h_idx_file_rev))
        db_dir_entry['revision'] = h_idx_file_rev

        self._save_db()

    def _read_db(self):
        fact = lambda: {
                        'revision': 0,
                        'cur_section': 0,
                        'last_vrec': -1,
                        }
        db = {'datadirs': defaultdict(fact),
              'cur_datadir': 'datadir0'}

        def obj_hook(d):
            if any(k.startswith('datadir') for k in d.keys()):
                dd = defaultdict(fact)
                dd.update(d)
                return dd
            return d

        try:
            with open(self._dbfile, 'r') as f:
                db_data = json.load(f, object_hook=obj_hook)
            db.update(db_data)
        except FileNotFoundError:
            pass

        LOG.debug('Finished reading db: {}'.format(db))

        return db

    def _save_db(self):
        LOG.debug('Saving db: {}'.format(self._db))

        with open(self._dbfile, 'w') as f:
            json.dump(self._db, f)

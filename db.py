from collections import defaultdict
import json
import logging
from pprint import pformat


logger = logging.getLogger(__name__)


def _dct_factoty():
    return {
        'cur_section': 0,
        'last_vrec': -1,
        'revision': 0,
    }


class DB():

    def __init__(self, db_fpath=None, db_decoder=None, db_encoder=None):
        super().__init__()

        self.db_fpath = db_fpath
        self.decoder = db_decoder or DBDecoder(self)
        self.encoder = db_encoder or DBEncoder(self)

        self._reset()
        if self.db_fpath is not None:
            self.load()

    def load(self):
        try:
            db_str = open(self.db_fpath, 'r').read()
            if db_str:
                db = self.decoder.decode(db_str)
                self._reset()
                self.update(db)
        except (FileNotFoundError, ValueError):
            logger.info('Could not load db from {}'.format(self.db_fpath))
        else:
            logger.debug('Finished loading db: {}'.format(self))

    def save(self):
        logger.debug('Saving db: {}'.format(self))

        with open(self.db_fpath, 'w') as db_file:
            for chunk in self.encoder.iterencode():
                db_file.write(chunk)

    def _reset(self):
        self._db = {'datadirs': defaultdict(_dct_factoty),
                    'cur_datadir': 'datadir0'}

    def __getattr__(self, attr):
        return getattr(self._db, attr)

    def __getitem__(self, item):
        return self._db.__getitem__(item)

    def __setitem__(self, item, value):
        return self._db.__setitem__(item, value)

    def __str__(self):
        return pformat(self._db)


class DBDecoder(json.JSONDecoder):

    def __init__(self, db, *args, **kwargs):
        super().__init__(object_hook=self._object_hook, *args, **kwargs)
        self.db = db

    def _object_hook(self, dct):
        if any(k.startswith('datadir') for k in dct.keys()):
            ddct = defaultdict(_dct_factoty)
            ddct.update(dct)
            return ddct
        return dct


class DBEncoder(json.JSONEncoder):

    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db

    def iterencode(self):
        return super().iterencode(self.db._db)

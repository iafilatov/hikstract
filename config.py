import configparser

_CFGFILE = 'config.cfg'

_DEFAULTS = {
            'main': {
                        'data_dir': '/mnt',
                        'output_dir': './out',
                        },
            'advanced': {
                         'avconv_args': '-c:v copy',
                         'db_file': 'index.db',
                         'h_index_file': 'index00.bin',
                         },
            }


class CFG(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure()
        
    def configure(self, cfgfile=_CFGFILE):
        self._load_defaults()
        self._read_file(cfgfile)
        
    def save(self, cfgfile=_CFGFILE):
        self._write_file(cfgfile)

    def _load_defaults(self):
        self.read_dict(_DEFAULTS)
    
    def _read_file(self, cfgfile):
        self.read(cfgfile)
        
    def _write_file(self, cfgfile):
        with open(cfgfile, 'w') as f:
            self.write(f)
            

cfg = CFG()
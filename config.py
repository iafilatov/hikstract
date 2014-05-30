import configparser

_CFGFILE = 'config.cfg'

_DEFAULTS = {
            'advanced': {
                         'avconv_args': '-c:v copy -v error',
                         'db_file': 'index.db',
                         'h_index_file': 'index00.bin',
                         },
            }

_MANDATORY = {
              'main': ('data_dir', 'output_dir'),
              }


class CFG(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure()
        self.validate()
        
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
            
    def validate(self):
        for sec, keys in _MANDATORY.items():
            if sec not in self:
                raise ConfigError('Section [{}] must be present in'
                                  ' config file'.format(sec))
            for k in keys:
                if k not in self[sec]:
                    raise ConfigError('Parameter `{}` must be present in'
                                      ' section [{}]'.format(k, sec))


class ConfigError(Exception):
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return self.msg
                

cfg = CFG()
hikstract
=========

Extracts videos recorded by Hikvision IP camera.


Configuration
-------------

All configuration is done inside `config.cfg`. Edit this file to suit your needs:

    # The directory, which the camera writes to
    data_dir = 
    
    # Output directory for extracted recordings
    output_dir = 
    
    # Debug logging
    debug = off
    
    # Extension of output files.
    # If no conversion is done, defaults to mp4 
    output_format = 
    
    # Take snapshots from extracted recordings in this format
    # Any format, supported by the chosen converter is possible 
    # Set to empty to disable
    snapshot_format = 
    
    # A/V converter to use, choices are: avconv, ffmpeg
    # Set to empty to preserve original stream
    converter = 


Usage
-----

Simply run `hikstract` from the command line.

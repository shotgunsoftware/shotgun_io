#!/usr/bin/env python

import shotgun_io
        
    
class ShotgunIOCustom (shotgun_io.ShotgunIOBase):
    """
    Class to manage Shotgun input and output specific to render queue workflow

    Inherits from the ShotgunIO class which allows you to override any of
    its methods to customize the workflow. 
    """
    def __init__(self, config, commandline): 
        super(ShotgunIOCustom, self).__init__()







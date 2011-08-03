######################
Customizing shotgun_io
######################
:mod:`shotgun_io` can be customized for your studio without requiring modification
of the base code. This obviously makes updating a lot easier as any custom
modifications that have been made for your studio won't be overwritten.

This will allow you to alter the default behavior of :mod:`shotgun_io` to match
your studio's workflow. 

For example, if you have a specific numbering convention that :mod:`shotgun_io`
doesn't handle out of the box, you can create your own custom :mod:`shotgun_io`
module that overrides the :py:func:`shotgun_io.ShotgunIOBase.get_next_version_number` method
to match your own needs.


Enabling your custom module
***************************
In order to enable your custom module, you'll have to create a new Python file
that subclasses :class:`shotgun_io.ShotgunIOBase`. This file must be saved in the
same location as **shotgun_io.py** and can be named anything you like. 

At a bare minumum, the file would look the the following::

    #!/usr/bin/env python

    import shotgun_io
            

    class ShotgunIOCustom (shotgun_io.ShotgunIOBase):
        """
        Custom ShotgunIO class to manage Shotgun input and output specific to 
        render queue workflow.

        This doesn't do anything different from the default ShotgunIOBase class
        since we're not overriding any methods, but we could ;) 
        """
        def __init__(self, config): 
            super(ShotgunIOCustom, self).__init__()

In addition to creating this file and placing it in the same directory as 
**shotgun_io.py**, you must enable the custom module in **shotgun_io.conf** by
setting the :ref:`custom_module <custom_module>` key to the name of your custom module filename
(minus the ``.py`` extension)

 

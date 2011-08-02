API usage
=========

ShotgunIO Factory
-----------------
While this class is the main class that gets called when creating a new instance,
it will normally return a :class:`ShotgunIOBase` instance which contains all of 
the default behavior for ShotgunIO. 

However, you may specify a custom module in the config that will override this
default behavior, in which case this will return a :class:`ShotgunIOCustom` 
instance which you (hopefully) have defined in your custom module. More info on 
that in the Customizing <customizing>_ section.

.. module:: shotgun_io

.. autoclass:: ShotgunIO
    :members:

ShotgunIOBase Class
-------------------
.. autoclass:: ShotgunIOBase
    :members:

ShotgunIOError Class
--------------------
.. autoclass:: ShotgunIOError
    :members:

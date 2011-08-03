.. shotgun_io documentation master file, created by
   sphinx-quickstart on Wed Jun 29 17:58:07 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

shotgun_io
======================================
This software was originally developed by `Shotgun 
Software <http://shotgunsoftware.com>`_ with support from `Greg Ercolano 
<http://seriss.com/people/erco/>`_. 

This software is provided under the BSD License that can be found in the LICENSE
file or here: http://www.opensource.org/licenses/bsd-license.php


Introduction
------------
The purpose of :mod:`shotgun_io` is to provide a simplified wrapper around the
Shotgun API to facilitate integrating render queues with Shotgun. By removing
the Shotgun-specific code from the render queue itself, it requires less effort
for vendors to add support for the integration, and makes it easy for studios 
to configure and update the integration piece independently of their render 
queue system. :mod:`shotgun_io` is the "go-between" sitting in the middle of your
Shotgun instance and your render queue system.

Should Shotgun add new features to it's product, the render queue companies are
not burdoned with going back and re-implementing lots of new hooks and code to
take advantage of them, rather shotgun_io can be updated by a studio and will 
automatically be able to take advantage of new features while still communicating
the same way with the render queue systems as it always did.

Additionally, :mod:`shotgun_io` enables studios to customize the way the integration
functions to match their specific workflow through configuration options or 
more advanced method overrides.

Documentation
-------------

.. toctree::
    :maxdepth: 2

    Configuration <configuration>
    Customizing  <customizing>
    Command line usage <cmdline>
    Python api usage <api>
    Integrating your render manager <softwarecos>




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


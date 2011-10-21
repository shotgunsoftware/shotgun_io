#########################################
Installing shotgun_io
#########################################
.. module:: shotgun_io

:mod:`shotgun_io` is intended to be the hub for managing communication between
render queue software and Shotgun. It wraps the Shotgun API to provide render 
specific commands and utilities to make integrating with Shotgun simple while
allowing studios the flexibility to customize the integration without requiring
them to touch any of the render queue code.

Customizations such as Shotgun authentication information, naming conventions,
etc. are all part of the :mod:`shotgun_io` package so you don't need to worry
about how to handle these types of configuration and customization options.

Integrating with Shotgun involves the following steps:

* enabling/disabling Shotgun integration
* adding Shotgun-specific menu options to submit windows
* creating/updating Versions in Shotgun
* passing job log information to **shotgun_io** for any custom processing

Installation
************
The :mod:`shotgun_io` package can be installed anywhere on your machine
provided that the following conditions are met:

1. Python (v2.4 up to v2.7) are installed
2. The machine has network access to your Shotgun server (for API calls)
3. The render queue manager can find and call shotgun_io from the command-line

For the purposes of this document and other examples presented, we'll assume
you'll want to install it inside ``/usr/local/shotgun``::

    $~ ls
    shotgun_io_v1.00b1.tar.gz

    $~ mkdir /usr/local/shotgun

    $~ tar -zxvf shotgun_io_v1.00b1.tar.gz -C /usr/local/shotgun
    x shotgun_io_v1.00b1/
    x shotgun_io_v1.00b1/docs/
    x shotgun_io_v1.00b1/docs/.buildinfo
    x shotgun_io_v1.00b1/docs/_sources/
    x shotgun_io_v1.00b1/docs/_sources/api.txt
    x shotgun_io_v1.00b1/docs/_sources/cmdline.txt
    x shotgun_io_v1.00b1/docs/_sources/configuration.txt
    x shotgun_io_v1.00b1/docs/_sources/customizing.txt
    x shotgun_io_v1.00b1/docs/_sources/index.txt
    x shotgun_io_v1.00b1/docs/_sources/softwarecos.txt
    x shotgun_io_v1.00b1/docs/_static/
    x shotgun_io_v1.00b1/docs/_static/basic.css
    x shotgun_io_v1.00b1/docs/_static/default.css
    x shotgun_io_v1.00b1/docs/_static/doctools.js
    x shotgun_io_v1.00b1/docs/_static/file.png
    x shotgun_io_v1.00b1/docs/_static/jquery.js
    x shotgun_io_v1.00b1/docs/_static/minus.png
    x shotgun_io_v1.00b1/docs/_static/nature.css
    x shotgun_io_v1.00b1/docs/_static/plus.png
    x shotgun_io_v1.00b1/docs/_static/pygments.css
    x shotgun_io_v1.00b1/docs/_static/searchtools.js
    x shotgun_io_v1.00b1/docs/_static/sidebar.js
    x shotgun_io_v1.00b1/docs/_static/underscore.js
    x shotgun_io_v1.00b1/docs/api.html
    x shotgun_io_v1.00b1/docs/cmdline.html
    x shotgun_io_v1.00b1/docs/configuration.html
    x shotgun_io_v1.00b1/docs/customizing.html
    x shotgun_io_v1.00b1/docs/genindex.html
    x shotgun_io_v1.00b1/docs/index.html
    x shotgun_io_v1.00b1/docs/objects.inv
    x shotgun_io_v1.00b1/docs/py-modindex.html
    x shotgun_io_v1.00b1/docs/search.html
    x shotgun_io_v1.00b1/docs/searchindex.js
    x shotgun_io_v1.00b1/docs/softwarecos.html
    x shotgun_io_v1.00b1/LICENSE
    x shotgun_io_v1.00b1/src/
    x shotgun_io_v1.00b1/src/io_entity_queries.py
    x shotgun_io_v1.00b1/src/io_entity_queries.pyc
    x shotgun_io_v1.00b1/src/io_input.py
    x shotgun_io_v1.00b1/src/io_input.pyc
    x shotgun_io_v1.00b1/src/io_output.py
    x shotgun_io_v1.00b1/src/io_output.pyc
    x shotgun_io_v1.00b1/src/shotgun_io.conf
    x shotgun_io_v1.00b1/src/shotgun_io.py

    $~ mv /usr/local/shotgun/shotgun_io_v1.00b1 /usr/local/shotgun/shotgun_io


Enabling Shotgun integration
****************************
In order to use :mod:`shotgun_io`, the render queue systems will need to know where it 
lives on the file system. This (and optionally other information) exists in the 
``.shotgun`` file. The ``.shotgun`` file can live wherever a studio wants it
to be. Therefore, in order to find where the ``.shotgun`` file lives, you can
assume there is a **SHOTGUN_CONFIG** environment variable that points to the 
location of the file. 

SHOTGUN_CONFIG environment variable
===================================
Studios are responsible for setting up a **SHOTGUN_CONFIG** environment variable 
that points to the location of the ``.shotgun`` file. Therefore, the first step
for setting up integration is to look for this environment variable. If it 
doesn't exist, integration cannot be enabled.

If it does exist, it should be a single absolute path to an existing readable
``.shotgun`` file. The format should look something like any of the following::

    SHOTGUN_CONFIG=/usr/local/etc/shotgun/.shotgun
    SHOTGUN_CONFIG=Z:\\fileserver\tools\.shotgun
    SHOTGUN_CONFIG=\\fileserver\tools\.shotgun

.. note:: Rush allows you to set this variable in the RushSiteSettings.py file as a convenience.

.shotgun file
=============
If the environment variable exists, the next step is to test that the ``.shotgun``
file exists and is readable. If the file does not exist or is not readable, the 
integration cannot be enabled.

Inside the ``.shotgun`` file there should be at least 2 settings:

* **enabled**: valid options are ``0`` to indicate the integration is not enabled, or ``1`` to indicate the integration is enabled
* **shotgun_io_bindir**: the absolute path to the directory where :mod:`shotgun_io` lives.

Example ``.shotgun`` file contents::

    enabled 1
    shotgun_io_bindir "/usr/local/etc/shotgun/shotgun_io/src"

The key and values must be separated by whitespace (don't use ``=`` , ``:``, etc.). The 
**shotgun_io_bindir** value must be a `double-quoted` path that points to the location of 
the ``shotgun_io.py`` script.

Handling additional variables
-----------------------------
If you need to use additional settings aside from the default variables in 
``.shotgun``, you may do so in a custom vendor-specific file named
``.shotgun_vendorname``. Additional vendor-specific variables *cannot* be stored
in the default ``.shotgun`` file. Decide on what the standard suffix will be for your
product and stick with it. For example, if your product name is "awesomesauce", 
you would look for a file named ``.shotgun_awesomesauce`` in the location
specified by the **SHOTGUN_CONFIG** environment_variable.

It is up to you if you require a custom ``.shotgun`` file or if you will use the
standard one by default, and only use your custom one if it exists. For example,
if you require the following additional variables

* **favorite_color**
* **lucky_number**

Your vendor-specific file would be ``.shotgun_awesomesauce`` and would look like
this::

    enabled 1
    shotgun_io_bindir "/usr/local/etc/shotgun/shotgun_io/src"
    favorite_color orange
    lucky_number 21
    
This overall structure lets studios to use multiple render management systems
with Shotgun integration but keeps any additional variables required by other
systems hidden.


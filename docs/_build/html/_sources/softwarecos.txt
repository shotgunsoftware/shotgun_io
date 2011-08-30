#########################################
Integrating your company's render manager
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

Enabling Shotgun integration
****************************
In order to use :mod:`shotgun_io`, your software will need to know where it 
lives on the file system. This (and optionally other information) lives in the 
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

.shotgun file
=============
If the environment variable exists, the next step is to test that the file
exists and is readable. If the file does not exist or is not readable, the 
integration cannot be enabled.

Inside the file there should be at least 2 settings:

* **enabled**: valid options are ``0`` to indicate the integration is not enabled, or ``1`` to indicate the integration is enabled
* **shotgun_io_path**: the absolute path to the directory where :mod:`shotgun_io` lives.

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
    shotgun_io_bindir: "/usr/local/etc/shotgun/shotgun_io/src"
    favorite_color orange
    lucky_number 21
    
This overall structure lets studios to use multiple render management systems
with Shotgun integration but keeps any additional variables required by other
systems hidden.


Adding Shotgun info to submit windows
=====================================
.. todo:: add a set of generic screens to show the desired UI and workflow.

There are only a couple of bits of Shotgun information that the artist will need 
to provide when submitting a job in order for the results to show up as a new
Version entity in Shotgun.


* **User name**: their username in Shotgun
* **Task**: the Task in Shotgun that they are working on for this job
* **Version name**: the name of the Version in Shotgun
* **Description**: an optional freeform text field for any additional info

From this information, :mod:`shotgun_io` can then figure out the Project and
Shot that the Task is for, assemble the correct Version name (with appropriate
Version number if configured for the studio), all enough to create the Version
in Shotgun (though the render manager will likely provide additional information
from the job as well).

We realize the UI framework for each piece of software is different, and has
varying features and limitations. So the following info is provided as a
guideline towards what we believe is a good example for usability.

The Shotgun info should be grouped together in a single area, preferably
requiring minimal clicks as artists don't like to mess around with more than
they need to. All of the fields should begin *disabled* until the artist has
provided their username and validated it. Once their username is validated, the
remaining fields should become enabled and where applicable, filled with the
valid information provided by :mod:`shotgun_io`.

Username
--------
* **field_type**: textbox with a button labeled "Connect" to the right

The artist should be able to type in their Shotgun username and either click
on the "Connect" button or hit the <return> key. This will initiate a call to 
:mod:`shotgun_io` to validate the user. The :func:`ShotgunIOBase.validate_user` method
can be used for this::

    io.validate_user('stewie')

If the user's id is returned this indicates the user is valid. The rest of the 
field should now be enabled. The Task menu should now be populated with all of 
the Tasks for the user. This can be done with :func:`ShotgunIOBase.get_entities`::

    io.get_entities('tasks', user_id=123)

Task
----
* **field_type**: dropdown list

:mod:`shotgun_io` will return a list of Tasks for the user which should populate
this dropdown menu for the artist to choose from. Because an artist could have
several Tasks in Shotgun with the same name, we provide some context that can
be used to help differentiate the Tasks from one another in the form of the 
Project and Shot.

Each task returned by :func:`ShotgunIOBase.get_entities` has enough info in
it to get the context.

* **task name** is represented by ``content``
* **project name** is represented by ``project['name']``
* **entity name** is represented by ``entity['name']``

The Tasks should be listed in the menu in the following format: 
``project name > entity name > task name``

When the artist selects a task, you need to store the associated ids for each.
In addition to the *id*, you also need to store the *type* of entity since a job
can be submitted for a Shot, Asset, Element or any other type of entity in 
Shotgun:

* **task id** (represented by ``id``)
* **project id** (represented by ``project['id']``)
* **entity id** (represented by ``entity['id']``)
* **entity_type** (represented by ``entity['type']``)

Version Name
------------
* **field_type**: editable dropdown list

An editable dropdown list is one where you can choose from a list of options, but can also edit that selection after you make it. 

.. note:: If your UI doesn't allow for an editable dropdown list you can use a combination of a dropdown list and an additional text field that shows the result.

In the **shotgun_io.conf** file, studio admins can define a set of Version name
templates so that artists don't have to name Versions manually. These templates
can contain tokens used for string replacement based on the values the artist
has chosen in the submit window. Valid tokens include:

==============  =====
tokens          value
==============  =====
``${project}``  name of the project in Shotgun
``${shot}``     name of the entity in Shotgun
``${task}``     name of the task in Shotgun
``${user}``     username in Shotgun
``${jobid}``    job_id as defined by render queue manager
==============  =====

You can get the list of defined templates using::

    >>> io.get_version_name_templates()
    ['', '${project}_${shot}_${task}', ' ${shot}_${task} ${jobid}']

The first option in the list is the default option an should be selected by
default in the UI. If the first option is an empty string, then there is no 
default assigned, and the user should be required to choose an option.

Before displaying the options in the menu, the tokens should be replaced by 
their actual values. If there is no value for the token, then simply use an
empty string. The artist should never see the actual token in its ``${token}``
form. 

If the UI is unable to handle updating the display values in the menu, it should
display the tokens minus the ``${}``. So ``${project}_${shot}`` would become 
``project_shot``.

For example, let's say user ``stewie`` is submitting a job for task
``Demo Project > 100_010 > Anim``. The table below shows you the version name
templates and the default value that should be displayed in the menu.

======================================= ========================================
template value                          actual value
======================================= ========================================
``${project}_${shot}_${task}``          ``Demo Project_100_010_Anim``
``${shot}_${task} (${user})``           ``100_010_Anim (stewie)``
``${project}/${shot}/${jobid}/${user}`` ``Demo Project/100_010/${jobid}/stewie``
======================================= ========================================

Notice in the last example we have actually broken the rule for showing raw
tokens in the menu display. We won't know the value for the ``${jobid}`` token 
until the job is submitted so this is the one exception to that rule.

.. warning:: While tokens *should* always have values for replacement, it is possible they may not. For example, Tasks can be without any link in Shotgun which would mean their entity value would be ``None``. This is an important consideration in ensuring your code does not generate an error. In this case, any tokens that don't have a value would simply be replaced with an empty string.

If you are using a separate text field for allowing the user to edit the version
name value, selecting a new version name template should overwrite the value
in the editable field.

Version numbering
^^^^^^^^^^^^^^^^^
Version numbering is handled automatically by :mod:`shotgun_io`. The studio
admins are responsible for configuring their own installation's version 
numbering scheme. Therefore you don't need to care about that at all, which we
hope is nice.

Description
-----------
* **field_type**: text box

The description field is a freeform text box that allows the artist to enter in 
any additional info they wish about the Version. There's no requirement to fill
this field in with info nor does it depend on any other input from the artist.


The render manager can provide the following additional information:

* **frames_path**
* **movie_path**
* **thumbnail_path**
* **first_frame**
* **last_frame**
* **frame_count**
* **frame_range**
* **status**
* **total_render_time**
* **avg_frame_time**

To see a full description of the valid fields allowed when creating and updating
Versions in Shotgun, see the section :ref:`valid_fields`.

 

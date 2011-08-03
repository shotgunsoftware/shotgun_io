##################
Configuration
##################

Configuration of ``shotgun_io`` is controlled by a single ``shotgun_io.conf``
file which comes pre-filled with default values suitable for most studios to
use out of the box. Most of the settings are relatively self-explanitory. This 
documentation is largely duplicated in the file itself. 

The file defines things like the url for your Shotgun server, script name, and
API key, field names to use, as well as some additional naming options.

Installation of the config file
*******************************
The ``shotgun_io.conf`` file must live either in the same directory as 
``shotgun_io.py`` or in the ``/etc`` directory. It will look for the conf file
in the current directory first, then in the ``/etc`` directory.


Shotgun server settings
***********************
url
===
The url location of your Shotgun server::

    url: https://myserver.shotgunstudio.com

script_name
===========
The script name used for API access. For more information, see `Setting up
Shotgun for API Access <https://github.com/shotgunsoftware/python-api/wiki/Setting-Up-Shotgun-for-API-Access>`_::

    script_name: shotgun_io

application_key
===============
The 40 character hex application key used for API access. For more information, 
see `Setting up Shotgun for API Access <https://github.com/shotgunsoftware/python-api/wiki/Setting-Up-Shotgun-for-API-Access>`_::

    application_key: 12345abcdef8992841c5045bbd404c6833c169f1

Version fields
**************
Define what field each piece of information will be stored in inside
of Shotgun. The conf file comes pre-filled with defaults that should
match most typical Shotgun server setups out of the box. There are some fields
that are not standard fields that would require adding a new field to your
Shotgun instance in order to use them. These options are not enabled by 
default.

If you don't want to store a particular piece of information, simply leave
it empty::

    no_value_here: 

.. note:: The Shotgun fields specified below must be configured as valid data types (ie. 
    you can only store text values in fields that are configured as text fields).  

name
====
Field that holds the Version name provided by the Artist in the submit dialog. 
(Example value: ``demo_100_010_anim_v001``)

.. note:: This is almost *always* going to be ``code`` and should only be 
    different if you have a unique workflow.

* **Valid data types**: text
* **Required?**: yes

Example::

    name: code

shot
====
Field that links to the entity the submitted Version is for. This could be a 
Shot or an Asset entity type. We name it "shot" for simplicity.

* **Valid data types**: entity
* **Required?**: yes

Example::

    shot: entity

job_status
==========
Field that stores the status of the render job. The status will be translated 
and updated in Shotgun on the Version entity. See the 'version_status' section below.

* **Valid data types**: status_list, list, text
* **Required?**: no

Example::

    job_status: sg_status_list

frames_path
===========
Field that stores the full path to the location of rendered frames in sequence 
notation (ie. ``/path/to/frames.#.jpg``). 

* **Valid data types**: text, file/link
* **Required?**: no

Example::

    frames_path: sg_path_to_frames

movie_path
==========
Field that stores the full path to the location of the proxy movie (ie. 
``/path/to/movie.mov``) 

* **Valid data types**: text, file/link
* **Required?**: no

Example::

    movie_path: sg_path_to_movie

upload_movie
============
If 'movie_path' is a file/link field, setting this to ``yes`` will upload the 
proxy movie to store in Shotgun instead of linking to it locally.

.. note:: This has no effect if the ``movie_path`` field is not a file/link (url) field.

* **Required?**: no

Example::

    upload_movie: yes

first_frame
===========
Field that stores the lowest frame number rendered by the job.

* **Valid data types**: number, float, text
* **Required?**: no

Example::

    first_frame: sg_first_frame

last_frame
==========
Field that stores the highest frame number rendered by the job.

* **Valid data types**: number, float, text
* **Required?**: no

Example::

    last_frame: sg_last_frame

frame_count
===========
Field that stores the count of all of the rendered frames in the job.

* **Valid data types**: number, float, text
* **Required?**: no

Example::

    frame_count: frame_count

frame_range
===========
Field that stores the frame range specified in the render job. The values can be a 
simple format (eg. ``1-100``), a complex format (eg. ``1-100,2``) or a mixture 
of formats separated by a single space (eg. ``1-100,2 200 300 351-400``)

* **Valid data types**: text
* **Required?**: no

Example::

    frame_range: frame_range

user
====
Field that links to the user who submitted the job and is creating the Version 
in Shotgun.

* **Valid data types**: entity (HumanUser)
* **Required?**: yes

Example::

    user: user

project
=======
Field that links to the Project the Version belongs to.

* **Valid data types**: entity (Project)
* **Required?**: yes

Example::

    project: project

task
====
Field that links to the Task in Shotgun the Version was created from. This is a
highly recommended workflow used to track the Versions generated for each Task.

Note that this is different from linking a Version to a shot (or entity). 

* **Valid data types**: entity (Task)
* **Required?**: no

Example::

    task: sg_task

job_id
======
Field that stores the render manager assigned id for the job. 

.. note:: this is a non-standard Shotgun field and is disabled by default. If 
    you want to store this information, you'll need to create a field in Shotgun
    and then enable this in the config file.

* **Valid data types**: text
* **Required?**: no

Example::

    job_id: sg_job_id

total_render_time
=================
Field that stores the total render time in seconds (wall clock time) it took to 
complete the job.

.. note:: this is a non-standard Shotgun field and is disabled by default. If 
    you want to store this information, you'll need to create a field in Shotgun
    and then enable this in the config file.

* **Valid data types**: number, float, text
* **Required?**: no

Example::

    total_render_time: sg_total_render_time

avg_frame_time
==============
Field that stores the average render time in seconds it took to render each 
frame in the job.

.. note:: this is a non-standard Shotgun field and is disabled by default. If 
    you want to store this information, you'll need to create a field in Shotgun
    and then enable this in the config file.

* **Valid data types**: number, float, text
* **Required?**: no

Example::

    avg_frame_time: sg_avg_frame_time

Version values
**************
Settings to control the format and values of information stored in Shotgun.

version_name_templates
======================
Comma-separated Version name templates to present to the Artist in the 
submit dialog dropdown menu. The first entry in this list will be selected
by default. If you don't want to specify a default, Insert a comma at the 
beginning of the list (eg. ``, ${project}_${shot}_${task}_v, ...``)

You can use the following tokens for automatic string replacement where available:

* ``${project}``: The name of the Project the Version is linked to in Shotgun (eg. ``Demo Project``)
* ``${shot}``: The display name of the Shot or Asset the Version is for  (eg. ``100_Intro_010``)
* ``${task}``: The name of the Task linked to the Version (eg. ``anim``)
* ``${user}``: login of the user creating the Version (eg. ``stewie``)
* ``${jobid}``: the id of the render job assigned by the render manager (eg. ``shadow_999_010_1234``)

Example::

    version_name_templates: ,${project}_${shot}_${task}, ${project}/${shot}/${task}/${user}, ${project} ${shot} ${task} ${jobid}, ${shot}_${task} ${jobid}

version_name_replace_spaces
===========================
If you want to replace spaces in the Version name, set this to ``yes`` and
provide the `version_name_space_token`_ below

Example::
    
    version_name_replace_spaces: yes

version_name_space_token
========================
If you want to replace spaces in the Version name with another character, specify
it here. Leave this blank to simply remove spaces.

Example::
    
    version_name_space_token: _

version_name_force_lowercase
============================
If you want to force Version names to be all lowercase, set this to ``yes``

Example::

    version_name_force_lowercase: yes

version_numbering
=================
Controls how Shotgun automatically adds Version numbers to submitted Versions.

``task`` will increment Version #s per Task::

    MyProject_100_010_bglayout_v1
    MyProject_100_010_anim_v1
    MyProject_100_010_bglayout_v2
    ...

``pipeline_step`` will increment Version #s per Pipeline Step::

    MyProject_100_010_layout_v1
    MyProject_100_010_anim_v1
    MyProject_100_010_layout_v2
    ...

``global`` will increment Version #s independent of Task so there will only be
a single Version with that #::

    MyProject_100_010_layout_v1, 
    MyProject_100_010_layout_v1
    MyProject_100_010_anim_v2
    MyProject_100_010_layout_v3
    ...

* **Valid values**: task, pipeline_step, global

Example::

    version_numbering: task

version_number_format
=====================
Formatting for version number. Standard string formating tokens can be used here 
as well as any plain string characters

Example::

    version_number_format: _v%03d

Will add on an appropriate version number suffix to the Version name::

    _v003


status_submitted
================
When a job is first submitted, the Version is created in Shotgun with this
status. Must be the short code of a valid enabled status value for the field 
specified for `job_status`_ above.

.. note:: These values are set to default status values in order to be compatible
    out of the box. 

Example::
    
    status_submitted: na

status_ip
=========
When a job is started, the associated Version record in Shotgun will be updated
with this status value. Must be the short code of a valid enabled status value 
for the field specified for job_status above.

Example::

    status_ip: ren

status_complete
===============
When a job is finishes without error, the associated Version record in Shotgun
will be updated with this status value. Must be the short code of a valid 
enabled status value for the field specified for job_status above.

Example::

    status_complete: rev

status_failed
=============
When a job is finishes with errors, the associated Version record in Shotgun
will be updated with this status value. Must be the short code of a valid 
enabled status value for the field specified for job_status above.

Example::

    status_failed: fail

scenefile_path_regexes
======================
.. warning:: this is unimplemented and will probably be removed or changed

Regexes for trying to automatically match project and shot in scenefile path.
Each regex pattern must have 2 groups. The first will always be the Project
the second must be the Shot/Asset

If a match is found for the Project and Shot/Asset, shotgun_io will lookup
the Tasks for the user for that Shot/Asset. If there is a single Task, that
Task should be the default Task selected in the submit UI. Otherwise the menu
will display all active Tasks for that user.

Example::

    scenefile_path_regexes: ^/\w*/\w*/\w*/\w*/(\w*)/(\w*), ^/\w*/\w*/something/\w*/(\w*)/(\w*)

scenefile_path_project_field
============================
.. warning:: this is unimplemented and will probably be removed or changed

Field name in Shotgun to match the project on.

Example::

    scenefile_path_project_field: project

scenefile_path_shot_field
============================
.. warning:: this is unimplemented and will probably be removed or changed

Field name in Shotgun to match the shot on.

Example::

    scenefile_path_shot_field: code


Advanced
********
workflow
========
The workflow defines how the artist will choose the Shotgun entity the
submitted job is for. The default workflow is ``task``. The artist will choose
the Task they are working on for this job and the Version created will be
linked to the entity the Task is linked to. The ``project_shot`` workflow adds 
menus to the Shotgun section of  submit windows for the artist to manually select 
the Project and Shot/Asset the job is for. 

* **valid options**: ``task`` (default), ``project_shot``

Example::

    workflow: task


.. _custom_module:

custom_module
=============
You may subclass :class:`shotgun_io.ShotgunIOBase` and override any of the methods in it as a custom 
module. Specify the module name here (ie. without the .py extention). This file 
must be in the same directory as :mod:`shotgun_io` (or in your $PYTHONPATH).

Example::

    custom_module: shotgun_io_custom







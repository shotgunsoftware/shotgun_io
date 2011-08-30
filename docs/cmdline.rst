##################
Command line usage
##################
``shotgun_io`` supports a simple command line interface. 

All normal output is sent to STDOUT and exits with a return code of ``0``. 
Any errors that are generated are send to STDERR and the script will exit with a 
return code of ``1``.

Available Commands
******************
List entities
=============
``-l --list``

.. function:: shotgun_io.py -l <entity_type> [-u <user_id> [-p <project_id>]]

Returns a list of entities from Shotgun of the specified type. This is primarily
used for populating a submit menu. For example, when an artist is submitting a job for a
specific Task, you would use this command to get the list of Tasks to populate
the menu with.

Some of the entity types require additional information for context. For example,
to list Tasks, you will also need to provide the id of the user to get tasks 
for: ``shotgun_io.py -l tasks -u 55``. 

However, other entity types require no context and can be retrieved with no 
additional information: ``shotgun_io.py -l projects``

 
Available entity types
----------------------
* ``users``
* ``projects``
* ``shots`` *requires project id* ``-p``
* ``assets`` *requires project id* ``-p``
* ``tasks`` *requires user id* ``-u``
* ``shotsandassets`` *requires user id* ``-u``

Additional switches
-------------------
* ``-p --project_id``
    project id for listing entity types that require a project id for context
* ``-u --user_id``
    user id for listing entity types that require a user id for context

Return values
-------------------
It can be assumed when parsing the output from any of these ``-l`` commands that
the leftmost output is unique identifier information like ids etc. used for 
creating and updating Shotgun information. Anything to the right of the first
whitespace is display information only (ie. Project names, Task names, etc.)

Generally the values returned are in the format ``id name`` where ``id`` is the
Shotgun id of the entity and ``name`` is the display name. The ``id`` is what you 
need to store for creating and updating Version values in Shotgun. There is a 
single space separating the ``id`` and the ``name``.

The exception to the general format is the output for Tasks. Since there are several
pieces of information provided in a Task, the format is 
``task_id,project_id,entity_type,entity_id project_name | entity name | task name``
Again, there is a single space separating unique identifiers from the display name

**General Example**::

    $ shotgun_io.py -l projects
    65 Demo Animation Project
    66 Awesome VFX Project
    70 Test Project 1

**General Output Breakdown**::

    70 Test Project 1
    \/|\____________/
    1 2      3

1. Project id
2. Space delimiting id output and display output
3. Project name

**Task Example**::

    $ shotgun_io.py -l tasks -u 39
    55,4,Asset,3 Demo Project | Asset 1 | Rig
    134,4,Asset,620 Demo Project | Asset 10 | Rig
    138,4,Asset,621 Demo Project | Asset 11 | Rig
    142,4,Asset,622 Demo Project | Asset 12 | Rig
    146,4,Asset,623 Demo Project | Asset 13 | Rig

**Task Output Breakdown**::

    147,4,Asset,623 Demo Project | Asset 13 | Surface Prep
    \_/ | \___/ \_/|\___________/  \______/   \__________/
     1  2   3    4 5      6            7           8
                    \____________________________________/
                                      9

1. Task id
2. Project id
3. Entity type
4. Entity id
5. Space delimiting id output and display output
6. Project name
7. Entity name
8. Task name
9. Complete Task name with Project and Entity context for menu
    
Get Version fields
==================
``-f --fields``

.. function:: shotgun_io.py -f

Returns a formatted list of internal field names for the Version entity in Shotgun. 
Fields are categorized by the field type and any internal fields that are not 
writeable are omitted. Field types are enclosed in ``[]``'s and followed by
field names that belong to that field type, one per line. Field type groups
are then separated by a single blank line

This can be useful for validating user input when configuring the integration.
For example, say a user if configuring the frames_path field which expects
text input. They specify a field name of ``'sg_foo'``. This command lets you 
see that ``sg_foo`` won't be a valid field for this type of information. Better
yet, if you use menus, then you can filter out the invalid field data types
from the list.

**Example**::

    $ shotgun_io.py -f
    [date_time]
    sg_render_timestamp

    [checkbox]
    sg_frames_have_slate
    sg_movie_has_slate

    [url]
    sg_file
    sg_link_to_frames
    sg_link_to_movie
    sg_uploaded_movie

    [text]
    code
    description
    frame_range
    sg_department
    sg_job_id
    sg_path_to_frames
    sg_path_to_movie

    [image]
    image

    [float]
    sg_frames_aspect_ratio
    sg_movie_aspect_ratio

    [list]
    sg_version_type

    [number]
    frame_count
    sg_avg_frame_time
    sg_first_frame
    sg_last_frame
    sg_total_render_time

    [entity]
    entity
    project
    sg_steve
    sg_task
    task_template
    user

    [multi_entity]
    notes
    playlists
    sg_storyboard_link
    task_sg_versions_tasks
    tasks

    [date]
    sg_render_datestamp

    [tag_list]
    tag_list

    [status_list]
    sg_status_list

Validate user
=========================
``-n --validate_user``

.. function:: shotgun_io.py -n <username>

Validates the Shotgun username and returns the corresponding user id. 

Useful for verifying the provided username is valid. The returned user id can be 
used to query for the valid Tasks for that user and can be saved to assign the 
artist to a Version created after the job.

When user is valid:

* **STDOUT**: Shotgun HumanUser id
* **STDERR**: Nothing
* **Exit code**: 0

When user is invalid:

* **STDOUT**: Nothing
* **STDERR**: Error message
* **Exit code**: 1
 
**Examples**::

    $ shotgun_io.py -u stewie
    34

    $ shotgun_io.py -u brian
    shotgun_io.py ERROR: User 'brian' is invalid.

Get workflow
=========================
``-w --workflow``

.. function:: shotgun_io.py -w

Returns the workflow config setting (``task`` or ``advanced``)

This is a convenience method for determining which workflow a studio is using
in order for render queues to determine what menu options to display to the
artist in submit windows.
 
**Examples**::

    $ shotgun_io.py -w
    task

Get Version status values
=========================
``-t --statuses``

.. function:: shotgun_io.py -t

Returns a list of valid status code values for Version entities. 

This can be useful for validating user input when configuring the integration.
Often there are config settings defining what status to set for a Version when
certain events occur (job submitted, job started, job complete, job failed). 
Any status value specified must be valid and in this list.

You can also minimize user error by using this command to populate a dropdown
list to eliminate the possibilities of invalid input and typos.

**Example**::

    $ shotgun_io.py -t
    na
    renq
    renip
    renf
    rev
    vwd

Get Version name templates
==========================
``-m --templates``

.. function:: shotgun_io.py -m

Returns a list of Version name templates defined in the config file. These
are used to populate the default name templates menu item. The first value
is the default and should be applied to the Version name immediately. If the
first value is '' then there is no default specified.

**Example**::

    $ shotgun_io.py -m
    ${project}_${shot}_${task}
    ${project}/${shot}/${task}/${user}
    ${project} ${shot} ${task} ${jobid}
    ${shot}_${task} ${jobid}


Get config values
=================
``--getconfig``

.. function:: shotgun_io.py --getconfig

Returns a list of current config values for shotgun_io categorized in sections.
Section names are listed in ``[]``'s followed by config settings for that section.
The key/value pair settings are formatted as ``key: value``. There is a blank
line following the last setting in each section.

**Example**::

    $ shotgun_io.py --getconfig
    [shotgun]
    url: https://awesomesauce.shotgunstudio.com
    application_key: 0123456789abcdef3e5db48065c79672c352cffd
    script_name: render_queue

    [version_values]
    version_name_templates: ,${project}_${shot}_${task}, ${project}/${shot}/${task}/${user}, ${project} ${shot} ${task} ${jobid}, ${shot}_${task} ${jobid}
    version_name_space_token: _
    status_submitted: queued
    version_name_force_lowercase: yes
    version_name_replace_spaces: yes
    version_numbering: task
    version_number_format: _v%03d
    status_ip: ren
    scenefile_path_regexes: ^/\w*/\w*/\w*/\w*/(\w*)/(\w*), ^/\w*/\w*/something/\w*/(\w*)/(\w*)
    status_failed: fail
    status_complete: rev

    [version_fields]
    job_status: sg_status_list
    project: project
    frames_path: sg_link_to_frames
    shot: entity
    job_id: sg_job_id
    total_render_time: sg_total_render_time
    avg_frame_time: sg_avg_frame_time
    frame_count: frame_count
    last_frame: sg_last_frame
    task: sg_task
    movie_path: sg_link_to_movie
    user: user
    upload_movie: no
    first_frame: sg_first_frame
    frame_range: frame_range
    name: code

    [shotgun_io]
    custom_module:

Create Version
==============
``-C --create_version``

.. function:: shotgun_io.py -C <version_info>
.. function:: shotgun_io.py -C /path/to/version_info.json
.. function:: shotgun_io.py -C <<EOF <version_info> EOF

Creates a new Version in Shotgun from the ``version_info`` key/value pairs.
Validation happens automatically and if successful, the command returns the id 
of the newly created Version.

``version_info`` is either a JSON formatted string of key/value pairs or the path
to a file that contains a JSON formatted string of key/value pairs. The key/value
pairs represent the field/value for the information to be contained in the Version.
Invalid keys will be silently ignored regardless of their data. Invalid data will 
generate an error if it is for a valid key.

Return Values
-------------
* Returns exit code ``0`` on success with Version id `int` value on STDOUT.
* Returns exit code ``1`` on failure with error message on STDERR. Nothing on STDOUT.

Required Fields
---------------
When creating a Version, the following fields are *required*:

* ``name``
* ``project``
* ``user``

.. _valid_fields:

Valid fields and formatting
---------------------------

user
^^^^
Shotgun id of the user (HumanUser) submitting the job. It must begin with a 
valid non-negative integer value corresponding to the id of a valid HumanUser 
(Person) record in Shotgun. It may have additional text following the id value
but must have a single space separating the id and any text following. 
Any text following the id will be ignored but is allowed for logging and debugging
purposes.

* **data_type**: `int` (`str`)
* **required on create?**: yes 
* **required on update?**: no 

**Examples**::

    {"user":"522"}
    {"user":"164 (fred)"}
    {"user":"23 kp(KevinPorterfield)"}
    {"user":"33 sarah#animationdepartment"}

task
^^^^
Shotgun id of the Task the Version is linked to. It must begin with a valid 
non-negative integer value corresponding to the id of a valid Task record in Shotgun.
It may have additional text following the id value but must have a single space 
separating the id and any text following. Any text following the id will be ignored 
but is allowed for logging and debugging purposes.

* **data_type**: `int` (`str`)
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"task":"2983"}
    {"task":"164 (DemoProject|100_010|Animation)"}
    {"task":"23 kpLighting_200_034[DemoProject]"}

project
^^^^^^^
Shotgun id of the Project in Shotgun the Version is linked to. It must begin with 
a valid non-negative integer value corresponding to the Shotgun id of a valid 
Project record in Shotgun. It may have additional text following the id value 
but must have a single space separating the id and any text following. Any text 
following the id will be ignored but is allowed for logging and debugging
purposes.

* **data_type**: `int` (`str`)
* **required on create?**: yes 
* **required on update?**: no 

**Examples**::

    {"project":"4"}
    {"project":"4 Demo Project"}
    {"project":"23 demo (Demo Project)"}

shot
^^^^
Shot or Asset this Shotgun Version is linked to. It must begin with a valid 
enabled Shotgun entity type string (currently ``Asset`` or ``Shot``) in CamelCase 
format. A single forward slash must immediately follow the entity type string.
A valid non-negative integer value corresponding to the Shotgun id of the entity
type record in Shotgun must immediately follow the forward slash. It may have 
additional text following the initial mandatory data but must have a single space 
separating the mandatory data and any text following. Any text following the 
mandatory data will be ignored but is allowed for logging and debugging purposes.

* **data_type**: `str`/`int` (`str`)
* **required on create?**: yes 
* **required on update?**: no 

**Examples**::

    {"shot":"Shot/164"}
    {"shot":"Shot/164 100_010"}
    {"shot":"Shot/164 DemoProject 100_010 ip"}
    {"shot":"Asset/2332"}
    {"shot":"Asset/2332 (FloorSpike)"}

name
^^^^
Name of the Version entity in Shotgun. It's highly recommended to be a string 
that describes the Project, Shot/Asset, Task (if available), and an incremental 
value. This allows Versions to be easily identifiable in Shotgun just by name.
If a hierarchical format is provided, it is also recommended to list the info in
increasingly specific order (ie. Project then Shot, then Task, etc.)

* **data_type**: `str`
* **required on create?**: yes 
* **required on update?**: no 

**Examples**::

    {"name":"demo_project_100_010_anim_v1"}
    {"name":"DemoProject/100_010/Animation/sarah_v1"}
    {"name":"demo_project_100_010_anim_v1job_id12345"}

description
^^^^^^^^^^^
Description field for the Version record in Shotgun to contain any arbitrary
text.

* **data_type**: `str`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"description":""}
    {"description":"still working on trying toget the penetration fixed, but all other notes are addressed."}
    {"description":"think this is the one"}

first_frame
^^^^^^^^^^^
The lowest frame number rendered by the job. The value should be a non-padded 
`int`. Negative numbers are okay.

* **data_type**: `int`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"first_frame":"1"}
    {"first_frame":"23"}
    {"first_frame":"-5"}

last_frame
^^^^^^^^^^
The highest frame number rendered by the job. The value should be a non-padded 
`int`. Negative numbers are okay.

* **data_type**: `int`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"last_frame":"100"}
    {"last_frame":"123"}
    {"last_frame":"-3"}

frame_count
^^^^^^^^^^^
The complete number of frames rendered by the job according to the ``frame_range``. 
The value should be a non-padded positive `int`. 

* **data_type**: `int`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"frame_count":"100"}
    {"frame_count":"50"}
    {"frame_count":"5"}

frame_range
^^^^^^^^^^^
String representation of what frames were rendered in the job. Must be in 
ascending numeric order. Multiple formats are supported. Combinations of formats 
must be separated by a single space. Spaces not allowed except when separating 
frame range formats. All frame values in the formats must be non-padded integer 
values.

* **data_type**: `int`
* **required on create?**: no 
* **required on update?**: no 

* standard syntax
    ``first_frame-last_frame``
* standard syntax with offset
    ``first_frame-last_frame,offset``
* single frame sequences
    ``first_frame another_frame another_frame``


**Examples**::

    {"frame_range":"1-100"}
    {"frame_range":"1-100,2"}
    {"frame_range":"1 23 55 59 123"}
    {"frame_range":"1-100 200-300"}
    {"frame_range":"1-100,2200-300 355"}
    {"frame_range":"24 100-130,2 201 250-300"}

frames_path
^^^^^^^^^^^
Full path to the rendered images output from the job. Must be absolute path. Use 
sequence notation placing # in the path to designate the frame number. Multiple 
paths may be specified but each path must appear on its own new line. May contain 
spaces in the pathname for Windows paths (but not recommended).

* **data_type**: `str`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"frames_path":"/server/path/to/frames.#.exr"}
    {"frames_path":"//otherserver/path/to/frames.low.#.jpg"}
    {"frames_path":"F:/path/to/SubDirectory/frames.#.tif"}
    {"frames_path":"//sillyserver/showfoo/path/to/frames.left.#.jpg"}
    {"frames_path":"//sillyserver/showfoo/path/to/frames.right.#.jpg"}

movie_path
^^^^^^^^^^
Full absolute path to the proxy movie output from the job. The path may contain 
spaces in the pathname for Windows paths (but not recommended).

* **data_type**: `str`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"movie_path":"/server/path/to/movie.mov"}
    {"movie_path":"//otherserver/path/to/movie.low.mov"}
    {"movie_path":"F:/path/to/SubDirectory/movie.mp4"}

job_id
^^^^^^
Render job id as defined by the render queue manager. Spaces are okay.

* **data_type**: `str`
* **required on create?**: yes 
* **required on update?**: yes 

**Examples**::

    {"job_id":"12345"}
    {"job_id":"saratoga.123"}
    {"job_id":"job rdfshadow.34fca90b11"}

job_status
^^^^^^^^^^
Numeric representation of the status of the render job used to translate to
the Version status in Shotgun
    
    * ``0`` = job submitted (any state that implies the job is running or may run in the future. This would include paused jobs.)
    * ``1`` = job running (job has been started and is in progress)
    * ``2`` = job completed (job completed in full successfully without any errors or failed frames) 
    * ``3`` = job failed (job has failed frames, had errors, or any other non-successful result status) 
    * ``4`` = job aborted (job was cancelled/dumped by user) 
    
    no other value is valid

The values of this field map to corresponding settings in the shotgun_io.conf 
file:

==========  =======================
job_status  shotgun_io.conf setting
==========  =======================
``0``       status_submitted:
``1``       status_ip:
``2``       status_complete:
``3``       status_failed:
``4``       status_aborted:
==========  =======================

If your job submissions are showing up as "n/a", be sure you've adjusted these
values in your shotgun_io.conf file.

* **data_type**: `int`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"job_status":"0"}
    {"job_status":"1"}
    {"job_status":"2"}
    {"job_status":"3"}
    {"job_status":"4"}


version_id
^^^^^^^^^^
*Not allowed in create*
Id of the Version to update as defined by Shotgun. Must be a non-padded positive 
integer and may not be blank.

* **data_type**: `int`
* **required on create?**: no *not allowed*
* **required on update?**: yes 

**Examples**::

    {"version_id":"12"}
    {"version_id":"4567"}


total_render_time
^^^^^^^^^^^^^^^^^
Total wall clock time in seconds from the time the job started to the time the
job completed. Must be a non-padded positive integer.

* **data_type**: `int`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"total_render_time":"120"}
    {"total_render_time":"4567"}

avg_frame_time
^^^^^^^^^^^^^^
Average wall clock time per frame in seconds from the time the frame
started to the time the frame completed. Must be a non-padded positive integer.

* **data_type**: `int`
* **required on create?**: no 
* **required on update?**: no 

**Examples**::

    {"avg_frame_time":"12"}


Update Version
==============
``-U --update_version``

.. function:: shotgun_io.py -U <version_info>
.. function:: shotgun_io.py -U /path/to/version_info.json
.. function:: shotgun_io.py -U <<EOF <version_info> EOF

Updates an existing Version in Shotgun from the ``version_info`` key/value pairs.
Validation happens automatically and if successful, the command returns the id 
of the newly created Version.

``version_info`` is either a JSON formatted string of key/value pairs or the path
to a file that contains a JSON formatted string of key/value pairs. The key/value
pairs represent the field/value for the information to be contained in the Version.
Invalid keys will be silently ignored regardless of their data. Invalid data will 
generate an error if it is for a valid key.

For valid fields and formatting, these are the same as the -C option, see 
:ref:`valid_fields` above.

Return Values
-------------
* Returns exit code ``0`` on success with Version id `int` value on STDOUT.
* Returns exit code ``1`` on failure with error message on STDERR. Nothing on STDOUT.

Required Fields
---------------
When updating a Version, the following fields are *required* in the
``version_info`` JSON string:

* ``version_id``


Delete Version
==============
``-D --delete_version``

.. function:: shotgun_io.py -D <version_id>
.. function:: shotgun_io.py --delete_version <version_id>

Deletes an existing Version in Shotgun with the id ``version_id``.

This command doesn not have any output by default. A warning is issued to STDERR 
if the Version exists but is *already* deleted, but will still return a ``0`` 
exit code.

Return Values
-------------
* Returns exit code ``0`` on success if Version was deleted or the Version was already deleted.
* Returns exit code ``1`` on failure with error message on STDERR if the Version with ``version_id`` does not exist. Nothing on STDOUT.

**Example**::

    $ shotgun_io.py -D 123


Process logfiles
=====================
``-x --logfiles``

.. function:: shotgun_io.py -x /path/to/logfiles/for/job -v <version_id>

.. note:: requires the additional ``-v`` switch for the ``version_id`` value.

This command should always be run at the successful completion of every job. It
will call any additional processing methods that are enabled for the vendor's 
software. This may do nothing, or may do lots of things.

Shotgun may provide additional functionality through this hook which will be 
maintained by Shotgun. In addition, individual studios may also hook into this 
call to enable additional custom processing they require.

Because of the "black box" nature of this command, vendors do not need to concern
themselves with the output or response of it. You can simply issue the command
and trust that anything else that is going to happen is out of your hands :)



 
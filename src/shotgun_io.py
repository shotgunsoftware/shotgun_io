#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------
# Copyright (c) 2009-2016, Shotgun Software Inc
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of the Shotgun Software Inc nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Provides interaction with Shotgun specific for render queue integrations.

ShotgunIO facilitates the creation and updating of Version entities in Shotgun.
It manages communication for listing entities in Shotgun for constructing job 
submission UIs, handles input and output formatting, and validation for creating
and updating Versions in Shotgun with render job specific information. 
"""

import sys
import os
import socket
import optparse
import ConfigParser
import logging
import re
import glob

try:
    import simplejson as json
except ImportError:
    import json
# shotgun_io modules
try:
    import io_entity_queries
except Exception, e:
    msg = "There is a problem in your entity_query_config module: %s" % e
    logging.error(msg)
    sys.exit(1)
import io_input
import io_output
try:
    import shotgun_api3
except ImportError, e:
    msg = "%s:\nThe Shotgun API is not installed. To install it, download the "\
        "latest version from https://github.com/shotgunsoftware/python-api, "\
        "extract the package and place it in this directory "\
        "or somewhere in your PYTHONPATH (more info on where to install modules "\
        "at http://docs.python.org/tutorial/modules.html#the-module-search-path)" % (e)
    logging.error(msg)
    sys.exit(1)

__author__ = "KP"
__copyright__ = "Copyright 2016, Shotgun Software"
__credits__ = ["Kevin Porterfield", "Greg Ercolano", "Kennedy Behrman"]
__license__ = "BSD"
__version__ = "1.0.0"
__maintainer__ = "KP"
__email__ = "kp@shotgunsoftware.com"
__status__ = "Production"

# LOGGING
# ====================================
class NullHandler(logging.Handler):
    """a NOP Logging handler that does nothing.
    """
    def emit(self, record):
        pass

    def handle(self, record):
        pass

logging.basicConfig(level=logging.INFO,
                    format="%(filename)s %(levelname)s: %(message)s" )
# shut up shotgun_api3 log messages
logging.getLogger('shotgun_api3').propagate = False
logging.getLogger('shotgun_api3').addHandler(NullHandler())
# setup our log
logging.getLogger(__name__)


# don't hang things up for more than 10 seconds if we can't reach Shotgun
socket.setdefaulttimeout(10)

# CONSTANTS (don't change these)
# ====================================
VERSION_STATUS_SUBMITTED = 0
VERSION_STATUS_IP = 1
VERSION_STATUS_COMPLETE = 2
VERSION_STATUS_FAILED = 3
VERSION_STATUS_ABORTED = 4
# minimum fields required to create a Version in Shotgun. 
REQUIRED_SG_VERSION_FIELDS = ['code','project','user']

NON_ENTITY_LIST_VALUES = ['entities']



class ShotgunIOError(Exception):
    """Base for all ShotgunIO Errors"""
    pass





class ShotgunIO(object):
    """Factory for ShotgunIO instance.

    A wrapper around the Shotgun API for creating and updating Versions and 
    managing Shotgun communication specific to render queue workflow. 

    Provides an easy way to get lists of entities from Shotgun for populating
    submit UI menus. Manages the input and output formatting of data as well as 
    validation for creating and updating Versions in Shotgun.

    Can be imported and instantiated directly or can be called standalone via 
    commandline. If a 'custom_module' is defined in shotgun_io.conf, attempts to 
    import the specified file and instantiate the ShotgunIOCustom class instead.
    
    :param config: ConfigParser instance holding configuration options loaded 
        from shotgun_io.conf
    :returns: ShotgunIO instance

    
    """
    
    def __new__(klass, **kwargs):
        # load config
        config = None
        config_paths = [os.path.abspath( os.path.dirname(__file__) ) + 
            "/shotgun_io.conf", '/etc/shotgun_io.conf']
        config = ShotgunConfigParser()
        config.read(config_paths)
        if not config:
            raise ShotgunIOError('shotgun_io.conf config file not found. ' \
                    'Searched %s' % (config_paths))


        # if no custom module is defined return the base class instance
        custom_module_str = config.get('advanced', 'custom_module')
        if not custom_module_str:
            return ShotgunIOBase(config)
        else:
            # attempt to load the custom module if enabled
            try:
                custom_module = __import__(custom_module_str)
            except ImportError:
                logging.warning("custom module '%s' specified in config not "\
                "found. Using the default ShotgunIO class instead.")
                return ShotgunIOBase(config)
            else:
                return custom_module.ShotgunIOCustom(config)


class ShotgunIOBase(object):
    """A wrapper around the Shotgun API for creating and updating Versions and 
    managing Shotgun communication specific to render queue workflow. 

    Provides an easy way to get lists of entities from Shotgun for populating
    submit UI menus. Manages the input and output formatting of data as well as 
    validation for creating and updating Versions in Shotgun 

    Can be imported and instantiated directly or can be called standalone via 
    commandline.
    
    :param config: ConfigParser instance holding configuration options loaded 
        from shotgun_io.conf
    :returns: ShotgunIOBase instance
    """
 
    def __init__(self, config): 
        
        self._config = config

        # shotgun server info
        self.shotgun_url = self._config.get('shotgun', 'url')
        self.shotgun_script = self._config.get('shotgun', 'script_name')
        self.shotgun_key = self._config.get('shotgun', 'application_key')
        self._sg = None
        
        # version numbering options
        self.version_numbering = self._config.get('version_values', 
                                                  'version_numbering')
        self.version_number_format = self._config.get('version_values', 
                                                      'version_number_format', 
                                                      1)

        # input and output validation and formatting
        self.input = io_input.InputDefault(self._config) 
        self.output = io_output.OutputDefault()


    def _shotgun_connect(self):
        """Instantiate Shotgun API for connecting to the Shotgun server and
        assign to this object's _sg variable.

        If instance already exists, no action is taken. Nothing is returned
        by this method.

        :raises: :class:`ShotgunIOError` on failure
        :todo: test this with the Shotgun JSON API.  
        """
        if self._sg:
            return       
        try:
            self._sg = shotgun_api3.Shotgun(self.shotgun_url, 
                            self.shotgun_script, self.shotgun_key)
        except Exception, e:
            raise ShotgunIOError("Unable to connect to Shotgun: %s" % e)


    def _validate_list_option(self, entity_type):
        """Validate the entity type requested is in the list of configured
        entity types.

        :returns: True if valid. False if invalid.
        :rtype: `bool`
        """
        if (entity_type in io_entity_queries.entity_queries.keys() or 
            entity_type in NON_ENTITY_LIST_VALUES):
            return True
        else:
            return False


    def _get_version_schema(self):
        """Internal method for introspecting the Version schema

        :returns: dictionary of all fields on the Version entity in the 
            default Shotgun API format
        :rtype: `dict`
        """
        self._shotgun_connect()
        try:
            schema = self._sg.schema_field_read('Version')
        except Exception, e:
            raise ShotgunIOError("Error getting Version schema: %s" % (e))

        return schema

    def get_workflow(self):
        """Returns the current configured workflow option as defined in the conf 
        file. 

        :returns: name of the workflow currently enabled 
        :rtype: `str`

        >>> io.get_workflow()
        task

        """
        w = self._config.get('advanced','workflow')
        return w

    def get_config(self):
        """Returns the current config option settings as defined in the conf 
        file. 

        :returns: Dictionary of current config settings as key value pairs 
        :rtype: `dict`
        """
        conf = {}
        for section in self._config.sections():
            conf[section] = {}
            for item in self._config.items(section, 1):
                conf[section][item[0]] = item[1]
        out = self.output.format_output('config', conf)

        return out
 

    def load_env_variables(self):
        """checks local environment variables for existance of SG_IO_* values
        and returns formatted key/value pairs.

        export SG_IO_USER='{"type":"HumanUser", "id":123, "login":"kp"}'
        export SG_IO_TASK='{"type":"Task", "id":234, "content":"Anim", "project":{"type":"Project","id":345,"name":"Demo Project"},"entity":{"type":"Shot","id":456,"name":"0010_0001"}}'
        export SG_IO_VERSION_NAME='010_0001 / anim / kp'
        export SG_IO_PROJECT='{"type":"Project", "id":123, "name":"Demo Project"}'
        export SG_IO_ENTITY='{"type":"Shot", "id":123, "name":"010_0001"}'

        :returns: Dictionary of key/value pairs representing Shotgun info
        :rtype: `dict`

        Example::

            >>> io.load_env_variables()
            {
            'user': {'type':'HumanUser', 'id':123},
            'task': {
                        'type':'Task', 
                        'id':234, 
                        'content':'Anim', 
                        'project': {'type':'Project', 'id':567},
                        'entity': {'type':'Shot', 'id':678}
                    },
            'name': '010_0001 / anim / kp',
            'project': {'type':'Project', 'id':345, 'name':'Demo Project'},
            'entity': {'type':'Shot', 'id':456, 'name':'0010_0001'}
            }
        """
        job_info = {}
        if os.environ.has_key("SG_IO_USER"):
            job_info['user'] = json.loads(os.environ.get('SG_IO_USER'))
        if os.environ.has_key("SG_IO_TASK"):
            job_info['task'] = json.loads(os.environ.get('SG_IO_TASK'))
        if os.environ.has_key("SG_IO_VERSION_NAME"):
            job_info['name'] = os.environ.get('SG_IO_VERSION_NAME')
        if os.environ.has_key("SG_IO_PROJECT"):
            job_info['project'] = json.loads(os.environ.get('SG_IO_PROJECT'))
        if os.environ.has_key("SG_IO_ENTITY"):
            job_info['shot'] = json.loads(os.environ.get('SG_IO_ENTITY'))
        # if os.environ.has_key("SG_IO_IMAGE_PATH"):
        job_info['image_path'] = os.environ.get('SG_IO_IMAGE_PATH')
        out = self.output.format_output('env_variables', job_info)

        return out



    def validate_user(self, username):
        """Checks if given username string is a valid active user in Shotgun. 

        If the username is active and valid, returns the id of the HumanUser 
        entity in Shotgun. If the username is invalid, returns None.

        >>> io.validate_user("zoe")
        42
        >>> io.validate_user("franny")
        shotgun_io.py ERROR: User 'franny' is invalid.
            
        :param username: the login to lookup in Shotgun
        :type username: `str`
        :returns: Shotgun id for the user or None if username wasn't found
        :rtype: `int` or `NoneType`
        :raises: :class:`ShotgunIOError` if the Shotgun query fails
        """
        self._shotgun_connect()
        io_entity_queries.validate_user['filters'].append(
            ['login', 'is', username])
        try:
            user = self._sg.find_one(
                    io_entity_queries.validate_user['entity_type'], 
                    io_entity_queries.validate_user['filters'], 
                    io_entity_queries.validate_user['fields'])
        except Exception, e:
            ShotgunIOError("Error validating user in Shotgun: %s" % (e))
        out = self.output.format_output('user', user)

        return out
                

    def get_version_fields(self):
        """Returns a dict of Version fields whose values are editable
        categorized by field type. 

        This may be useful for introspecting whether specified field names 
        defined during setup or configuration of the integration when done
        interactively. 
        
        :returns: dictionary of the editable fields for the Version entity in 
                    Shotgun grouped by field type
        :rtype: `dict`
        :raises: :class:`ShotgunIOError` if the Shotgun query fails

        :todo: The filtering could be more intelligent at filtering out 
            additional fields that don't make sense
        
        Example::

            >>> io.get_version_fields()
            {'checkbox': ['sg_frames_have_slate', 'sg_movie_has_slate'],
             'date': ['sg_render_datestamp'],
             'date_time': ['sg_render_timestamp'],
             'entity': ['entity',
                        'project',
                        'sg_task',
                        'task_template',
                        'user'],
             'float': ['sg_frames_aspect_ratio', 'sg_movie_aspect_ratio'],
             'list': ['sg_version_type'],
             'multi_entity': ['notes',
                              'playlists',
                              'sg_storyboard_link',
                              'task_sg_versions_tasks',
                              'tasks'],
             'number': ['frame_count',
                        'sg_avg_frame_time',
                        'sg_first_frame',
                        'sg_last_frame',
                        'sg_total_render_time'],
             'status_list': ['sg_status_list'],
             'tag_list': ['tag_list'],
             'text': ['code',
                      'description',
                      'frame_range',
                      'sg_department',
                      'sg_job_id',
                      'sg_path_to_frames',
                      'sg_path_to_movie'],
             'url': ['sg_link_to_frames',
                     'sg_link_to_movie',
                     'sg_uploaded_movie']}

        """
        self._shotgun_connect()
        sorted_fields = {}

        try:
            fields = self._sg.schema_field_read('Version')
        except Exception, e:
            raise ShotgunIOError("Error retrieving list of Version fields from"\
                                 " Shotgun: %s" % (e))
        
        # sort fields by data_type. remove fields that aren't editable.
        for fn, fv in fields.iteritems():
             if fv['editable']['value']:
                try:
                    sorted_fields[fv['data_type']['value']].append(fn)
                except KeyError:
                    sorted_fields[fv['data_type']['value']]=[]
                    sorted_fields[fv['data_type']['value']].append(fn)
        
        # sort the field names in each type
        for t, f in sorted_fields.iteritems():
            f.sort()

        out = self.output.format_output('version_fields', sorted_fields)

        return out


    def get_version_status_values(self):
        """Returns a list of valid status values for the Version Status field 
            in Shotgun

        :returns: list of short codes for the configured status field in Shotgun
        :rtype: `list`
        :raises: :class:`ShotgunIOError` if the Shotgun query fails

        >>> io.get_version_status_values()
        ['na', 'queued', 'ren', 'rev', 'vwd', 'fail']

        """
        self._shotgun_connect()
        try:
            status_field = self._sg.schema_field_read(
                                    'Version','sg_status_list')
        except Exception, e:
            logging.error("Error retrieving list of valid status values for "\
                          "Versions from Shotgun: %s" % (e))
        
        out = self.output.format_output('version_statuses', 
                status_field['sg_status_list']['properties']['valid_values']['value'])

        return out


    def get_version_name_templates(self):
        """Return a list of the Version name templates defined in the config.

        The first entry in the list is the default. If the first
        entry is blank, then there is no default set.

        Allows tokens like ${project} or ${shot} that can be used
        for string replacement in the submit UI. 

        :returns: list of Version name templates defined in the config
        :rtype: `list`

        >>> print io.get_version_name_templates()
        ['', '${project}_${shot}_${task}', ' ${shot}_${task} ${jobid}']

        """
        template_list = []
        template_list = self._config.get(
                                'version_values',
                                'version_name_templates').split(',')

        out = self.output.format_output('version_name_templates', template_list)

        return out
         

    def get_entities(
            self, entity_type, project_id=None, user_id=None, no_format=False):
        """Retrieve a list of entities of `entity_type` from Shotgun

        The config file holds several settings for how this query is executed
        including filters, fields returned, sorting options, and whether the 
        project_id and user_id is required. These settings are controlled by 
        the studio to match their workflow. Vendors can assume that the
        settings will define the details for the studio and shouldn't 
        concern themselves with them.

        :param entity_type: type of entities to query Shotgun for
        :type entity_type: `str`

        :param project_id: id of the project to limit the query to. This is
            required for certain entity types (like Shots and Assets)
        :type project_id: `int`
        
        :param user_id: id of the user to limit the query to. This is 
            required for certain entity types (like Tasks)
        :type user_id: `int`
        
        :param no_format: used internally
        :type no_format: `bool`
        
        :returns: list of Shotgun entity dictionaries matching the default 
            settings defined in the config
        :rtype: `list`
        
        :raises: :class:`ShotgunIOError` if the validation fails or the Shotgun 
            query fails

        Example::

            >>> io.get_entities("tasks", user_id=55)
            [{'content': 'Anm',
              'entity': {'id': 860, 'name': 'bunny_010_0010', 'type': 'Shot'},
              'id': 557,
              'project': {'id': 65, 'name': 'Demo Animation Project', 'type': 'Project'},
              'type': 'Task'}]        
        
        """
        if not self._validate_list_option(entity_type):
            raise ShotgunIOError("entity_type value '%s' is invalid. Valid "\
                                 "options are %s" % 
                                 (entity_type, 
                                 io_entity_queries.entity_queries.keys()+NON_ENTITY_LIST_VALUES))
        entities = []

        # advanced workflow: potentially run multiple queries
        if entity_type == "entities":
            for t in io_entity_queries.advanced_workflow_entities:
                entities += self.get_entities(t, project_id=project_id,
                                              no_format=True)
        else:
            filters = io_entity_queries.entity_queries[entity_type]['filters']
            # check if we need to inject project or user filters
            if io_entity_queries.entity_queries[entity_type]['project_required']:
                if project_id is None:
                    raise ShotgunIOError("'project_id' is a required parameter"\
                                         " for getting '%s'" % entity_type)
                filters.append(
                    ['project', 'is', {'type':'Project', 'id': project_id}]
                    )

            if io_entity_queries.entity_queries[entity_type]['user_required']:
                if user_id is None:
                    raise ShotgunIOError("'user_id' is a required parameter "\
                                         "for getting '%s'" % entity_type)
                if entity_type == 'tasks':
                    filters.append(
                        ['task_assignees', 'is', 
                        {'type':'HumanUser', 'id':user_id}])
                elif entity_type == 'projects':
                    # we could add a filter for Projects the user is linked to 
                    # but if this is overridden by permissions, we have no way 
                    # of knowing that from the API. So when we do, add that 
                    # logic here.
                    pass

            self._shotgun_connect()
            try:
                entities = self._sg.find(
                        io_entity_queries.entity_queries[entity_type]['entity_type'], 
                        filters=filters, 
                        fields=io_entity_queries.entity_queries[entity_type]['fields'], 
                        order=io_entity_queries.entity_queries[entity_type]['order'])
            except Exception, e:
                raise ShotgunIOError("Error retrieving %s list from Shotgun: "\
                                     "%s" % (entity_type, e))
            else:
                # in a recursive call to combine entity lookups we'll do the
                # formatting when we're all done
                if no_format:
                    return entities
                
        out = self.output.format_output(entity_type, entities)
        return out


    def get_entities_from_file_path(self, scene_path):
        # """Attemps to match a Project and Shot name automatically from the scene 
        # file path based on regex definitions in the shotgun_io config.

        # This method is a good candidate for overriding in 
        # :class:`ShotgunIOCustom` since there's often varying logic that needs to
        # be implemented for each studio.

        # Currently just returns strings for project and shot which can then
        # be used to lookup their entity ids in Shotgun. Returns None if no match 
        # was found.

        # .. warning:: This method is not implemented

        # :param scene_path: full path to the scene path
        # :type entity_type: `str`

        # :raises: NotImplementedError

        # :returns: tuple with project and shot 
        # :rtype: `tuple`
        # """
        raise NotImplementedError("This method isn't implemented")
        
        ret = None
        for r in self.scenefile_path_regexes:
            result = re.match(r, scene_path)
            if result:
                project, shot = result.groups()
                if project and shot:
                    ret = (project, shot)

        out = self.output.format_output('scenepath_parse', ret)

        return out
        

    def get_next_version_number(self, entity, task=None):
        """Calculates the next Version number based on the pending Version
        that is about to be created.

        The logic used depends on what the setting for ``version_numbering`` is
        in the config. 

        .. note:: If the config specifies Task-based numbering and no Task
            is provided, it will fall back on global numbering.

        :param entity: Shotgun entity the Version is for. The format is the 
            standard Shotgun entity hash format with a required 'type' and 'id'
            key in the dictionary. Eg. ``{'type':'Shot', 'id':123}``
        :type entity: `dict`
        :param task: Task entity required for Task-based or Pipline Step-based
            numbering. Format is the standard Shotgun entity hash format with 
            a required 'type' and 'id' key in the dictionary. Eg. 
            ``{'type':'Task', 'id':456}``
        :type task: `dict` or `None`
        :returns: the next Version number for the Version contained in this 
            instance
        :rtype: `int`

        """
        self._shotgun_connect()
        next_number = 1
        step = None
 
        filters = [['entity', 'is', entity]]        
        
        # task-based numbering: add task filter
        if self.version_numbering == 'task':
            tf = self._config.get('version_fields', 'task')
            if task:
                filters.append([tf, 'is', task])
        
        # pipeline step-based numbering: add step filter
        elif self.version_numbering == 'pipeline_step':
            # lookup pipeline step for provided task and append appropriate
            # filter
            if task:
                result = self._sg.find_one(
                                'Task', 
                                [['id', 'is', task['id']]], 
                                ['step'])
                if result:
                    step = result['step']                    
                filters.append(['%s.Task.step' % tf, 'is', step])
        
        result = self._sg.find("Version", filters, ['code'], 
                    order=[{'field_name':'content','direction':'asc'}])
        
        for v in result:
            match = re.search('v(\d*$)',v['code'])
            if match and len(match.groups())==1:
                version_number = int(match.group(1))
                if version_number >= next_number:
                    next_number = version_number+1

        return next_number


    def create_version(self, version_data):
        """create new Version entity in Shotgun from the provided Version data

        If the ``version_data`` is a JSON `str`, this will automatically 
        perform JSON decoding prior to validation, and data translation of the
        data to the expected Shotgun API format based on the integration 
        environment.

        :param version_data: structured data representing field/value pairs for
            creating the new Version. Input formats can vary depending on
            implementation. Eg. this can be a `str` JSON string or a Python
            `dict`
        :type version_data: `str` or `dict`

        :raises: :class:`ShotgunIOError` if validation fails or Shotgun query 
            fails.
        """
        ret = {}
        self.input.action = 'create'
        self.input._version_schema = self._get_version_schema()

        # turn JSON string into valid dictionary hash
        self.input.extract_version_data(version_data)

        # check required fields (sometimes project and shot will be part of the
        # task need to handle that)
        for f in REQUIRED_SG_VERSION_FIELDS:
            if not f in self.input.shotgun_input:
                raise ShotgunIOError("Unable to create Version in Shotgun. "\
                                     "Missing required Shotgun field '%s'" % f)

        # append next version number formatted as defined
        if self.version_numbering:
            entity = self.input.shotgun_input.get(
                        self._config.get('version_fields', 'shot'))
            task = self.input.shotgun_input.get(
                        self._config.get('version_fields', 'task'))
            version_number = self.get_next_version_number(entity, task)
            if version_number:
                self.input.shotgun_input['code'] += self.version_number_format \
                                                    % (version_number)
        
        # create version
        self._shotgun_connect()
        try:
            version = self._sg.create('Version', self.input.shotgun_input)
            ret.update(version)
        except Exception, e:
            raise ShotgunIOError("Error creating Version in Shotgun: %s" % e)
        else:
            if self.input.thumbnail_path is not None:
                result = self.upload_thumbnail(version['id'], 
                                               self.input.thumbnail_path)
                if result:
                    ret['thumbnail_id'] = result
            if self.input.movie_upload is not None:
                result = self.upload_movie(version['id'], 
                                     self.input.movie_upload)
                if result:
                    ret.update(result)

        return self.output.format_output('version_create', ret)


    def update_version(self, version_data):
        """Update existing Version entity in Shotgun from the provided Version 
        data.

        If the ``version_data`` is a JSON `str`, this will automatically 
        perform JSON decoding prior to validation, and data translation of the
        data to the expected Shotgun API format based on the integration 
        environment.

        :param version_data: structured data representing field/value pairs for
            creating the new Version. Input formats can vary depending on
            implementation. Eg. this can be a `str` JSON string or a Python
            `dict`. Requires ``id`` key with integer value that 
            corresponds to the id of the Version entity to  update in Shotgun.
        :type version_data: `str` or `dict`

        :raises: :class:`ShotgunIOError` if validation fails or Shotgun query 
            fails.
        """
        ret = {}
        self.input.action = 'update'
        self.input._version_schema = self._get_version_schema()

        self.input.extract_version_data(version_data)

        # check required fields
        if 'id' not in self.input.shotgun_input:
            raise ShotgunIOError("Unable to update Version in Shotgun. Missing"\
                                 " required field 'version_id' in Version hash")
        
        # extract Version id and remove it from the dict
        version_id = self.input.shotgun_input['id']
        del(self.input.shotgun_input['id'])

        # check if we are uploading a thumbnail
        if self.input.thumbnail_path is not None:
            result = self.upload_thumbnail(version_id, 
                                           self.input.thumbnail_path)
            if result:
                ret['thumbnail_id'] = result

        # check if we are uploading a movie
        if self.input.movie_upload is not None:
            result = self._sg.upload(version_id, self.input.movie_upload)
            if result:
                ret.update(result)

        # check if we have anything else to update
        if len(self.input.shotgun_input) == 0:
            return ret

        # update version
        self._shotgun_connect()
        try:
            version = self._sg.update('Version', 
                                      version_id, self.input.shotgun_input)
            ret.update(version)
        except Exception, e:
            raise ShotgunIOError("Error updating Version in Shotgun: %s" % e)
        
        return self.output.format_output('version_update', ret)


    def upload_thumbnail(self, version_id, frames_path):
        """Upload file located at thumb_path as thumbnail for Version with 
        version_id
        """
        self._shotgun_connect()
        print "uploading thumbnail from %s" % frames_path
        # /Users/kp/Documents/shotgun/maya/horse_gallop/frames/horseGallop_final.iff.#
        # replace frame syntax with regex
        pattern = re.sub('[#@]', '[0-9]', frames_path)
        # lookup output frames that match our pattern
        files = glob.glob(pattern)
        # nothing matched? We should generate an error here
        if len(files) == 0:
            logging.error("no matching frames were found to upload thumbnail. "\
                        "searched %s" % pattern)
            return False
        print "found frames"
        
        frame_choice = self._config.get('version_values', 'thumbnail_frame')
        if frame_choice == 'first':
            thumb_frame = files[0]
        elif frame_choice == 'last':
            thumb_frame = files[-1]
        else:
        # middle frame is the default
            thumb_frame = files[ len(files)/2 ]

        # check that thumb_path exists and is readable.
        if not os.path.exists(thumb_frame):
            raise ShotgunIOError("Error uploading thumbnail '%s' to Shotgun "\
                                 "for Version %d: thumbnail path not found." % \
                                 (thumb_frame, version_id))
            return False

        print "found thumbnail frame %s" % thumb_frame
        # upload thumbnail
        try: 
            result = self._sg.upload_thumbnail('Version', version_id, thumb_frame)
        except Exception, e:
            raise ShotgunIOError("Error uploading thumbnail '%s' to Shotgun "\
                                 "for Version %d: %s" % \
                                 (thumb_frame, version_id, e))
            return False
        print "done"
        return self.output.format_output("thumbnail_id", result)


    def upload_movie(self, version_id, movie_path):
        """Upload file located at movie_path to Version with 
        version_id
        """
        self._shotgun_connect()
        # check that movie_path exists and is readable.
        if not os.path.exists(movie_path):
            raise ShotgunIOError("Error uploading movie '%s' to Shotgun "\
                                 "for Version %d: movie path not found." % \
                                 (movie_path, version_id))
            return False
        
        # upload movie to movie field
        movie_field = self._config.get("version_fields","movie_path")
        try: 
            result = self._sg.upload('Version', version_id, movie_path,
                                     movie_field)
        except Exception, e:
            raise ShotgunIOError("Error uploading thumbnail '%s' to Shotgun "\
                                 "for Version %d: %s" % \
                                 (movie_path, version_id, e))
            return False

        return self.output.format_output("movie_upload", {movie_field: result})


    def delete_version(self, version_id):
        """Delete existing Version entity in Shotgun with the provided Version 
        id.

        Deletes (or 'retires' in Shotgun lingo) the Version with id 
        ``version_id``. Only useful for cases where a user cancels or dumps
        a render job and the associated Version in Shotgun would be irrelevant.
        Deleting the Version ensures there is no extra cruft lying around.


        :param version_id: Shotgun id of the Version to be deleted.
        :type version_data: `int`

        :returns: `True` if the Version was deleted. `False` if no Version with 
            id ``version_id`` exists

        .. note:: if the ``version_id`` does not exist, the Shotgun API spits
            out an error response to STDERR
        """
        self._shotgun_connect()
        if not isinstance(version_id, int):
            raise ShotgunIOError('version_id must be an integer')

        try:
            result = self._sg.delete('Version', version_id)
        except shotgun_api3.Fault, e:
            raise ShotgunIOError('Error deleting Version #%d: %s' \
                % (version_id, e))
        else:
            return self.output.format_output("version_delete", result)

    def process_logfiles(self, logfiles):
        raise NotImplementedError("processing logfiles will be enabled before "\
            "release at least to not generate errors.")



class ShotgunIoOptionParser(optparse.OptionParser):
    """error(msg : string)

    Print a usage message incorporating 'msg' to stderr and exit.
    If you override this in a subclass, it should not return -- it
    should either exit or raise an exception.

    subclassed to make exit code 1 instead of 0.
    """
    def error(self, msg):
        self.print_usage(sys.stderr)
        self.exit(1, "%s: error: %s\n" % (self.get_prog_name(), msg))

    """override format_description to not strip newlines
    """
    def format_description(self, formatter):
        return self.get_description()


class ShotgunConfigParser(ConfigParser.SafeConfigParser):
    # def __init__(self):
    #     super(ShotgunConfigParser, self).__init__()

    def getlist(self, section, option, sep=",", chars=None):
        """Return a list from a ConfigParser option. By default, split on a 
        comma and strip whitespaces. Do not interpolate any % characters
        """
        
        return [chunk.strip(chars) 
                for chunk in self.get(section, option, 1).split(sep)]


def check_options(option, opt_str, value, parser):
    """does simple check for valid option combinations when called from the 
    command line

    This is not a very robust method but does some basic checking to ensure
    that more than one action isn't being attempted at the same time.
    """
    exclusive_options = [
        'list', 'fields', 'create_version', 'update_version', 'statuses', 
        'logfiles', 'templates', 'getconfig', 'delete_version','env_vars'
        ]
    boolean_options = [
        'fields', 'statuses', 'templates', 'getconfig', 'workflow','env_vars'
        ]

    for o in exclusive_options:
        if getattr(parser.values, o):
            raise ShotgunIOError("%s option cannot be used when '--%s' option "\
                "has already been specified" % (opt_str, o))

    if option.dest in boolean_options:
        setattr(parser.values, option.dest, True)
    else:
        setattr(parser.values, option.dest, value)

def read_options():
    """defines options when shotgun_io is called from the commandline
    """
    # options  
    usage = "USAGE: %prog [options]\nTry %prog --help for more information"
    version_string = "v%s (%s)" % (__version__, __status__)
    full_version_string = "%prog " + version_string
    description = "%prog provides a simplified wrapper around the Shotgun API to facilitate integrating render queues with Shotgun.\n\n"+full_version_string 
    parser = ShotgunIoOptionParser(usage=usage, version=full_version_string, description=description)
    parser.add_option("-l", "--list", type="string", default=None, action="callback", callback=check_options, help="retrieve a list of entities from Shotgun")
    parser.add_option("-p", "--project_id", type="int", default=None, help="required Project id when using '-l (--list)' option with entities that are Project specific (assets, shots, etc.)")
    parser.add_option("-u", "--user_id", type="int", default=None, help="required HumanUser id when using '-l (--list) tasks'")
    parser.add_option("-n", "--validate_user", type="string", default=None, help="test whether provided username is valid - returns user id and username when valid, nothing when invalid")
    parser.add_option("-C", "--create_version", type="string", default=None, action="callback", callback=check_options, help="create Version in Shotgun. Value must be a valid JSON encoded hash with required keys")
    parser.add_option("-U", "--update_version", type="string", default=None, action="callback", callback=check_options, help="update Version in Shotgun. Value must be a valid JSON encoded hash with at least a version_id key (for the Version to update)")
    parser.add_option("-D", "--delete_version", type="int", default=None, action="callback", callback=check_options, help="delete Version in Shotgun. Value is an integer representing the Shotgun id of the Version to be deleted")
    parser.add_option("-f", "--fields", dest="fields", action="callback", callback=check_options, help="return a list of valid fields and field types on the Version entity for storing information.")
    parser.add_option("-t", "--statuses", dest="statuses", action="callback", callback=check_options, help="return a list of valid status values for Versions")
    parser.add_option("-x", "--logfiles", type="string", default=None, action="callback", callback=check_options, help="path to logfiles for processing")
    parser.add_option("-v", "--version_id", type="int", default=None, help="Shotgun Version id required when using '-x (--logfiles)' option to process logfiles")
    parser.add_option("-m", "--templates", dest="templates", action="callback", callback=check_options, help="return a list of Version name templates defined in shotgun_io.conf")
    parser.add_option("-w", "--workflow", dest="workflow", action="callback", callback=check_options, help="return the current workflow setting defined in the config (default is 'task')")
    parser.add_option("-e", "--env", dest="env_vars", action="callback", callback=check_options, help="returns preset Shotgun vars if they are already decided by context")
    parser.add_option("--getconfig", dest="getconfig", action="callback", callback=check_options, help="display the current config values from shotgun_io.conf")

    return parser


def main():
    """Handles execution of shotgun_io when called from the command line
    """

    parser = read_options()
    (options, args) = parser.parse_args()
    
    io = ShotgunIO()
    io.input = io_input.InputCmdLine(io._config)
    io.output = io_output.OutputCmdLine()

    if options.env_vars:
        print io.load_env_variables()

    # list entities
    elif options.list:
        if not io._validate_list_option(options.list) and options.list not in NON_ENTITY_LIST_VALUES:
            raise ShotgunIOError("--list value '%s' is invalid. Valid "\
                                 "options are %s" % 
                                 (options.list, 
                                 io_entity_queries.entity_queries.keys()+NON_ENTITY_LIST_VALUES))
        if (options.list == 'entities' or \
            io_entity_queries.entity_queries[options.list]['project_required']) and \
            options.project_id == None:
            raise ShotgunIOError("-l (--list) option '%s' requires a project id: -p (--project_id)" % options.list)

        elif options.list in ['tasks'] and options.user_id == None:
            raise ShotgunIOError("-l (--list) option '%s' requires a user id: -u (--user_id)" % options.list)

        else:
            print io.get_entities(options.list, project_id=options.project_id, user_id=options.user_id)
            
    # validate username
    elif options.validate_user:
        out = io.validate_user(options.validate_user)
        if not out:
            raise ShotgunIOError("User '%s' is invalid." % options.validate_user)
        print out

    # list fields
    elif options.fields:
        print io.get_version_fields()

    # list valid status values
    elif options.statuses:
        print io.get_version_status_values()

    # create Version in Shotgun
    elif options.create_version:
        print io.create_version(options.create_version)

    # update Version in Shotgun
    elif options.update_version:
        print io.update_version(options.update_version)

    # delete Version in Shotgun (no ouput)
    elif options.delete_version:
        io.delete_version(options.delete_version)

    # process logfiles
    elif options.logfiles:
        if options.version_id is None:
            raise ShotgunIOError("-x (--logfiles) option also requires a Version id: -v (--version_id)")
        print io.process_logfiles(options.logfiles)

    # list version name templates
    elif options.templates:
        print io.get_version_name_templates()

    # get config vals
    elif options.getconfig:
        print io.get_config()
 
    # get workflow
    elif options.workflow:
        print io.get_workflow()

    else:
        parser.print_help
        if len(sys.argv) > 1:
            raise ShotgunIOError("invalid option combination '%s'. The '%s' "\
                "switch probably requires another switch to be provided.\n\n"\
                "Try '%s --help' to see the valid options" % 
                (sys.argv[1],sys.argv[1],os.path.basename(__file__)))
        else:
            parser.print_usage(sys.stderr)
            raise ShotgunIOError("At least one option is required. No options specified")
            # list options here




if __name__ == '__main__':
    # executed only when called from the command line
    try:
        main()
    # runtime errors
    except ShotgunIOError, e:
        logging.error(e)
        sys.exit(1)
    # validation errors
    except ValueError, e:
        logging.error(e)
        sys.exit(1)
    # configuration errors
    except ConfigParser.NoOptionError, e:
        logging.error('There is a problem with your configuration file. '\
            'You are missing a required option. %s' % e)
        sys.exit(1)
    except ConfigParser.NoSectionError, e:
        logging.error('There is a problem with your configuration file. '\
            'You are missing a section header (it should look like '\
            '[section_header]). %s' % e)
        sys.exit(1)
    # import errors
    except ImportError, e:
        logging.error('You are missing required Python modules: %s' % e)
        sys.exit(1)
    # unimplemented errors
    except NotImplementedError, e:
        logging.error('This command is not yet implemented: %s' % e)
        sys.exit(0)
    
    sys.exit(0)



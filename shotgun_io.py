#!/usr/bin/env python

# ./shotgun_io.py -C "{\"user\":\"32 kp\",\"task\":\"2,4,Shot,2 Demo Project | Shot 1 | Match Move\",\"name\":\"Demo Project_Shot 1_Match Move v3 kp contrail.123\",\"description\":\"fixing penetration for blah.\n- this was done\n- this still needs work\n-b lah\",\"jobid\":\"contrail.123\", \"job_status\":\"0\"}"
# ./shotgun_io.py -U "{\"version_id\":\"5\",\"first_frame\":\"1\",\"last_frame\":\"100\",\"frame_range\":\"1-50 61-70,2 80 90 100\",\"frame_count\":\"58\",\"frames_path\":\"/path/to/frames/image.#.jpg\",\"movie_path\":\"/path/to/movie/popcorn.mov\",\"jobid\":\"contrail.123\", \"job_status\":\"1\"}"

import time # for benchmarking
timer = { 'start': time.time() }
# ====================================
# CONSTANTS (don't change these)
# ====================================
VERSION_STATUS_SUBMITTED = 0
VERSION_STATUS_COMPLETE = 1
VERSION_STATUS_FAILED = 2

# ====================================
# VARIABLES
# ====================================

entity_config = {
    'users': {
        'entity_type': 'HumanUser',
        'filters': [['sg_status_list', 'is_not', 'dis']],
        'fields': ['id','login'],
        'order': [{'field_name':'login','direction':'asc'}],
        'project_required': False,
        },
    'projects': {
        'entity_type': 'Project',
        'filters': [['sg_status', 'is_not', 'Archive'],['name', 'is_not', 'Template Project']],
        'fields': ['id','name'],
        'order': [{'field_name':'name','direction':'asc'}],
        'project_required': False,
        },
    'assets': {
        'entity_type': 'Asset',
        'filters': [['sg_status_list', 'is_not', 'omt']],
        'fields': ['id','code'],
        'order': [{'field_name':'code','direction':'asc'}],
        'project_required': True,
        },
    'shots': {
        'entity_type': 'Shot',
        'filters': [['sg_status_list', 'is_not', 'omt']],
        'fields': ['id','code'],
        'order': [{'field_name':'code','direction':'asc'}],
        'project_required': True,
        },
    'tasks': {
        'entity_type': 'Task',
        'filters': [],
        'fields': ['id','content','entity','project'],
        'order': [{'field_name':'project','direction':'asc'},{'field_name':'entity','direction':'asc'},{'field_name':'content','direction':'asc'}],
        'project_required': False,
        },
    'assetsandshots': {
        'project_required': True,
        'user_required': False,
    },
    'projectsandtasks': {
        'project_required': False,
        'user_required': True,
    },
}

# minimum fields required to create a Version in Shotgun. These aren't the Shotgun field names but the
# keys passed into this script that get translated to Version fields.
required_version_fields = ['name','project','user']
required_sg_version_fields = ['code','project','user']

version_field_map = {
    'name': 'code',
    'shot': 'entity',
    'description': 'description',
    'job_status': 'sg_status_list',
    'frames_path': 'sg_path_to_frames',
    'movie_path': 'sg_path_to_movie',
    'first_frame': 'sg_first_frame',
    'last_frame': 'sg_last_frame',
    'frame_count': 'frame_count',
    'frame_range': 'frame_range',
    'user': 'user',
    'project': 'project',
    'task': 'sg_task',
    'entity': 'entity',
}

version_name_templates = [
    '${project}_${shot}_${task}_v',
    '${project}/${shot}/${task}/${user} v',
    '${project} ${shot} ${task} ${jobid}',
    '${shot}_${task} ${jobid}',
    ]

version_status_map = {
    VERSION_STATUS_SUBMITTED: 'na',
    VERSION_STATUS_FAILED: 'na',
    VERSION_STATUS_COMPLETE: 'rev',
}

# ====================================
# END VARIABLES 
# ====================================

import sys
import os
import socket
import pprint
import optparse
import datetime
import logging
# imports of json and shotgun modules are handled below

# don't hang things up for more than 10 seconds if we can't reach Shotgun
socket.setdefaulttimeout(10)

def bail(errmsg=''):
    logging.error(errmsg)
    sys.exit(1)


def validate_list_option(option):
    non_entity_options = ['version_name_templates']
    if option in entity_config.keys() or option in non_entity_options:
        return True
    else:
        bail("-l (--list) option must be a valid option:\n%s" % (entity_config.keys()+non_entity_options))


def isEntityHash(value, allow_none=True):
    if value == None and allow_none:
        return True
    
    result = isinstance(value, dict)
    if result:
        result = 'type' in value and 'id' in value
        if result:
            result = isinstance(value['type'], str) and isinstance(value['id'], int)
            if result:
                result = value['type'] in ['Asset','Shot']
    
    return result 

def isString(value, allow_blank=True):
    result = isinstance(value, str) or isinstance(value, unicode)
    if result:
        if not allow_blank:
            result = value.strip() != ''
    
    return result 

def isInt(value, allow_zero=False):
    result = isinstance(value, int)
    if result:
        if not allow_zero:
            result = value != 0

    return result

def formatRushEntities(listtype, vals):
    timer['reformat_rush_start'] = time.time()
    ret = ""
    # users
    # id login
    if listtype == 'users':
        for u in vals:
            ret += "%d %s\n" % (u['id'], u['login'])
    
    elif listtype == 'tasks':
        for t in vals:
            p_id = p_name = ""
            e_id = e_name = e_type = ""
            # verify Task has a Project
            if isinstance(t['project'], dict):
                p_id = t['project']['id']
                p_name = t['project']['name']
            # verify Task has an entity
            if isinstance(t['entity'], dict):
                e_id = t['entity']['id']
                e_type = t['entity']['type']
                e_name = t['entity']['name']
            ret += "%s,%s,%s,%s %s | %s | %s\n" % (t['id'], p_id, e_type, e_id, p_name, e_name, t['content'])

    elif listtype == 'projects':
        for p in vals:
            ret += "%d %s\n" % (p['id'], p['name'])

    elif listtype == 'projectsandtasks':
        print "Rush output format for 'projectsandtasks' is not yet implemented"
        # for p in vals:
        #     ret += "%d %s\n" % (p['id'], p['name'])

    elif listtype == 'shots' or listtype == 'assets' or listtype == 'assetsandshots':
        for s in vals:
            ret += "%d %s\n" % (s['id'], s['code'])
    
    elif listtype == 'statuses':
        for s in vals:
            ret += "%s\n" % (s)
    timer['reformat_rush_end'] = time.time()
    return ret

        
    
class ShotgunIO (object):
    def __init__(self, shotgun_url, shotgun_script, shotgun_key):
        self.shotgun_url = shotgun_url
        self.shotgun_script = shotgun_script
        self.shotgun_key = shotgun_key
        self._sg = None

        self.version_as_json = None
        self.version_as_dict = None
        self.version_translated = None


    def _shotgun_connect(self):
        """
        Instantiate Shotgun class for connecting to the Shotgun server
        """
        timer['connect_start'] = time.time()
        try:
            self._sg = shotgun_api3.Shotgun(self.shotgun_url, self.shotgun_script, self.shotgun_key)
        except Exception, e:
            bail("Unable to connect to Shotgun: %s" % e)
        else:
            timer['connect_end'] = time.time()
            return True




    def listVersionNameTemplates(self):
        """Return a list of the defined Version name templates

        The first entry in the list is the default. If the first
        entry is blank, then there is no default set.

        Allows tokens like ${project} or ${shot} that can be used
        for string replacement based on choices in the submit tool. 
        """
        return "\n".join(version_name_templates)
        # return "%s\n" % (n) for n in version_name_templates



    def listEntities(self, entity_type, **kwargs):
        """
        Retrieve a list of entities from Shotgun and return them in a hash format.
        eg.
            [{'id':1, 'type':'Project', 'name':'Project Awesome'},
             {'id':2, 'type':'Project', 'name':'Project Wicked'}]
        """
        timer['listEntities_start'] = time.time()
        entities = []
        # special case: combine two calls and return combo
        if entity_type == "assetsandshots":
            kwargs['no_format']=True
            for t in ['shots','assets']:
                entities += self.listEntities(t, **kwargs)
            entities = formatRushEntities(entity_type, entities)
            return entities
        elif entity_type == "projectsandtasks":
            kwargs['no_format']=True
            for t in ['projects','tasks']:
                entities += self.listEntities(t, **kwargs)
            entities = formatRushEntities(entity_type, entities)
            return entities
        else:
            filters = entity_config[entity_type]['filters']
            # check if we need to inject project or user filters
            if entity_config[entity_type]['project_required']:
                filters.append(['project', 'is', {'type':'Project', 'id': kwargs['project_id']}])

            if 'user_id' in kwargs and kwargs['user_id']:
                if entity_type == 'tasks':
                    filters.append(['task_assignees', 'is', {'type':'HumanUser', 'id': kwargs['user_id']}])
                elif entity_type == 'projects':
                    # we could add a filter for Projects the user is linked to but
                    # if this is overridden by permissions, we have no way of knowing that 
                    # from the API. So when we do, add that logic here.
                    pass

            if not self._sg:
                self._shotgun_connect()
            try:
                entities = self._sg.find(entity_config[entity_type]['entity_type'], filters=filters, fields=entity_config[entity_type]['fields'], order=entity_config[entity_type]['order'])
            except Exception, e:
                timer['listEntities_end'] = time.time()
                bail("Error retrieving %s list from Shotgun: %s" % (entity_type, e))
            else:
                timer['listEntities_end'] = time.time()
                if 'no_format' in kwargs and kwargs['no_format']:
                    return entities
                
                return formatRushEntities(entity_type, entities)
                

    

    def listVersionFields(self):
        """
        Returns a dict of editable Version fields categorized by field type. 

        The key is the string field type and the value is a list of string field
        names. Internal and non-editable fields are filtered out automatically.
        
        ##TODO: The filtering could be more intelligent.
        """
        sorted_fields = {}
        if not self._sg:
            self._shotgun_connect()
        try:
            fields = self._sg.schema_field_read('Version')
        except Exception, e:
            bail("Error retrieving list of Version fields from Shotgun: %s" % (e))
        
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

        return sorted_fields


    def listVersionStatusValues(self):
        """
        Returns a list of valid status values for the Version Status field
        
        """
        sorted_fields = {}
        if not self._sg:
            self._shotgun_connect()
        try:
            status_field = self._sg.schema_field_read('Version','sg_status_list')
        except Exception, e:
            bail("Error retrieving list of valid status values for Versions from Shotgun: %s" % (e))
        
        return status_field['sg_status_list']['properties']['valid_values']['value']


    def _validateVersionData(self, field, value):
        """
        Validate the data provided for the given Version field. 

        Check that required values exist and the value is the correct data type.
        """
        isok = False
        if field == 'name':
            isok, msg = (isString(value, False), "'%s' key value (%s) is not a valid non-empty string" % (field, value))
        
        if field == 'entity_id':
            isok, msg = (isInt(value, False), "'%s' key value (%s) is not a valid non-zero integer" % (field, value))

        if field == 'entity_type':
            isok, msg = (isString(value, False), "'%s' key value (%s) is not a valid non-empty string" % (field, value))

        # elif field == 'shot':
        #     isok, msg = (isEntityHash(value, True), "'%s' key value (%s) is not a valid entity hash" % (field, value))
        
        elif field == 'task':
            isok, msg = (isInt(value, False), "'%s' key value (%s) is not a valid non-zero integer" % (field, value))

        elif field == 'project':
            isok, msg = (isInt(value, False), "'%s' key value (%s) is not a valid non-zero integer" % (field, value))

        elif field == 'user':
            isok, msg = (isInt(value, False), "'%s' key value (%s) is not a valid non-zero integer" % (field, value))

        elif field == 'description':
            isok, msg = (isString(value, True), "'%s' key value (%s) is not a valid string" % (field, value))

        elif field == 'job_status':
            isok, msg = (isInt(value, True), "'%s' key value (%s) is not a valid integer" % (field, value))
            if isok:
                isok, msg = (value in version_status_map, "'%s' key value (%s) is not in defined valid statuses (%s)" % (field, value, version_status_map.keys()))
            if isok:
                valid_version_statuses = self.listVersionStatusValues()
                isok, msg = (version_status_map[value] in valid_version_statuses, "'%s' key value %d (%s) is not enabled in Shotgun on the Version entity. Valid statuses are: %s" % (field, value, version_status_map[value], valid_version_statuses))

        elif field == 'frames_path':
            isok, msg = (isString(value, True), "'%s' key value (%s) is not a valid string" % (field, value))
        
        elif field == 'movie_path':
            isok, msg = (isString(value, True), "'%s' key value (%s) is not a valid string" % (field, value))

        elif field == 'first_frame':
            isok, msg = (isInt(value, True), "'%s' key value (%s) is not a valid integer" % (field, value))

        elif field == 'last_frame':
            isok, msg = (isInt(value, True), "'%s' key value (%s) is not a valid integer" % (field, value))

        elif field == 'frame_count':
            isok, msg = (isInt(value, True), "'%s' key value (%s) is not a valid integer" % (field, value))

        elif field == 'frame_range':
            isok, msg = (isString(value, True), "'%s' key value (%s) is not a valid string" % (field, value))
        
        else:
            # we could continue here without error but push a warning instead
            isok = False
            return (False, "Unknown key '%s' in Version hash" % field)
        
        if not isok:
            if msg:
                # return (False, msg)
                bail("Error during validation of Version data: %s" % msg)
            else:
                # return (False, "Invalid data for key '%s' in Version hash" % field)
                bail("Invalid data for key '%s' in Version hash" % field)
            
        return True


    def _translateVersionDataRush(self, version_hash):
        """
        Translation method to convert Version data provided by Rush to the common Shotgun format.

        Runs validation method _validateVersionData() as part of translation which will bail if
        the data is invalid.

        ##TODO: make these product-specific translations into modules to include with a one-liner
                based on the studio's config or environment the script is run with.
        """
        version_data = {}
        for f, v in version_hash.iteritems():
             # task is a special case that contains multiple id values
             ##TODO: this would be better if we could recursively call this method to assign translate 
             #       each key individually. 
            if f == 'task':
                keys = v.split(' ')[0]
                task_id, project_id, entity_type, entity_id = keys.split(",")
                task_id = int(task_id)
                project_id = int(project_id)
                entity_id = int(entity_id)
                self._validateVersionData('task', task_id)
                self._validateVersionData('project', project_id)
                self._validateVersionData('entity_type', entity_type)
                self._validateVersionData('entity_id', entity_id)
                # task
                version_data[ version_field_map[f] ] = {'type':'Task', 'id': int(task_id)}
                # project
                version_data[ version_field_map['project'] ] = {'type':'Project', 'id': int(project_id)}
                # entity
                if entity_type != '' and entity_id != '':
                    version_data[ version_field_map['entity'] ] = {'type':entity_type, 'id': int(entity_id)}
            else:
                # integer values
                if f in ['user','shot','project','first_frame','last_frame','frame_count','entity_id', 'job_status']:
                    value = int(v.split(' ')[0])
                else:
                    value = v

                # we have the value, now validate it
                self._validateVersionData(f, value)
                
                if f == "user":
                    version_data[ version_field_map[f] ] = {'type':'HumanUser', 'id': value}

                elif f == 'shot':
                    version_data[ version_field_map[f] ] = {'type':'Shot', 'id': value}

                elif f == 'project':
                    version_data[ version_field_map[f] ] = {'type':'Project', 'id': value}

                elif f == 'job_status':
                    self._validateVersionData(f, value)
                    version_data[ version_field_map[f] ] = version_status_map[value]
                
                # data is fine as is
                elif f in version_field_map:
                    version_data[ version_field_map[f] ] = value

                else:
                    # if we've hit this, there's no field translation so 
                    # the config tells us we're not storing this information
                    # and we ignore nicely.
                    pass
        
        return version_data


    def _decodeVersionHash(self, version_hash):
        """
        convert JSON string representation of Version into Python object.
        """
        try:
            return json.loads(version_hash)
        except ValueError, e:
            bail("invalid JSON format provided for Version: %s" % e)


    def createVersion(self, version_hash):
        """
        create new Version entity in Shotgun from the provided JSON-encoded Version data

        performs JSON decoding, validation, and data translation to the expected Shotgun format
        based on the integration environment.

        ##TODO: remove hard-coded Rush format in favor of a dynamic translation module provided
                at runtime.
        """
        # turn JSON string into valid dictionary hash
        version_hash = self._decodeVersionHash(version_hash)

        # translate data
        version_data = self._translateVersionDataRush(version_hash)

        # check required fields (sometimes project and shot will be part of the task need to handle that)
        for f in required_sg_version_fields:
            if not f in version_data:
                bail("Unable to create Version in Shotgun. Missing required Shotgun field '%s'" % f)
                
        # translate data
        # version_data = self._translateVersionDataRush(version_hash)

        # create version
        if not self._sg:
            self._shotgun_connect()
        try:
            version = self._sg.create('Version', version_data)
        except Exception, e:
            bail("Error creating Version in Shotgun: %s" % e)
        
        return version


    # Will probably be any unknown amount of info defined by the _translateVersionDataRush method and dump
    # anything extra out. Will always require a Version id.
    def updateVersion(self, version_hash):
        """
        Update existing Version entity in Shotgun with the provided JSON-encoded Version data

        performs JSON decoding, validation, and data translation to the expected Shotgun format
        based on the integration environment. Requires 'id' key with integer value that corresponds
        to the id of the Version entity to update in Shotgun.

        ##TODO: remove hard-coded Rush format in favor of a dynamic translation module provided
                at runtime.
        """
        # turn JSON string into valid dictionary hash
        version_hash = self._decodeVersionHash(version_hash)

        # translate data
        version_data = self._translateVersionDataRush(version_hash)

        # check required fields
        if 'version_id' not in version_hash:
            bail("Unable to update Version in Shotgun. Missing required field 'version_id' in Version hash")
        
        vid = int(version_hash['version_id'])

        # update version
        if not self._sg:
            self._shotgun_connect()
        try:
            version = self._sg.update('Version', vid, version_data)
        except Exception, e:
            bail("Error updating Version in Shotgun: %s" % e)
        
        return version

class ShotgunIoOptionParser(optparse.OptionParser):
    """error(msg : string)

    Print a usage message incorporating 'msg' to stderr and exit.
    If you override this in a subclass, it should not return -- it
    should either exit or raise an exception.
    """
    def error(self, msg):
        self.print_usage(sys.stderr)
        self.exit(1, "%s: error: %s\n" % (self.get_prog_name(), msg))


def load_modules():
    """
    load the (possibly) non-standard Python modules and provide info and/or alternative
    modules if the first choice isn't found.
    """

    # try to load the json module which is a default module in Python v2.6+
    # if it's not found, fall back on simplejson if it's available.
    try:
        import json
    except ImportError, e:
        try:
            import simplejson as json
        except ImportError:
            python_version = "%d.%d.%d" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
            msg = "No supported JSON module is installed. It's a standard module as of Python 2.6. If you are " \
                    "running an earlier version of Python (yours is v%s), you can download and install the "\
                    "simplejson module from http://pypi.python.org/pypi/simplejson. If you have a package "\
                    "manager on your system you can use something like `apt-get install python-simplejson` "\
                    "or if you have the setuptools module installed in Python, just type `easy_install simplejson`" % python_version
            bail(msg)
    
    # try to load the shotgun api. If it's not found, provide useful error about how to get it.
    try:
        import shotgun_api3
    except ImportError:
        msg = "The Shotgun API is not installed. To install it, download the latest version from "\
                "https://github.com/shotgunsoftware/python-api/downloads, extract the package and place the "\
                "shotgun_api3.py file in this directory or somewhere in your PYTHONPATH (more info on where to "\
                "install modules at http://docs.python.org/tutorial/modules.html#the-module-search-path)"
        bail(msg)
    
    return (json, shotgun_api3)

if __name__ == '__main__':
    # setup logging
    timer['main'] = time.time()
    log_format = "%(filename)s %(levelname)s: %(message)s"
    logging.basicConfig(format=log_format, level=logging.DEBUG)

    # load non-standard modules
    json, shotgun_api3 = load_modules()

    # options  
    ##TODO: do more robust error checking for mutually exclusive options
    ##TODO: add option to read input from STDIN
    usage = "usage: %prog [options]"
    parser = ShotgunIoOptionParser(usage=usage)
    parser.add_option("-S", "--shotgun_url", type="string", default=None, help="URL of your Shotgun server including the 'http(s)://'")
    parser.add_option("-s", "--shotgun_script", type="string", default=None, help="Script Name entity to use for API authentication")
    parser.add_option("-k", "--shotgun_key", type="string", default=None, help="Script Application Key to use for API authentication")
    parser.add_option("-l", "--list", type="string", default=None, help="retrieve a list of entities from Shotgun")
    parser.add_option("-p", "--project_id", type="int", default=None, help="required Project id when using '--list assets', or '--list shots'")
    parser.add_option("-u", "--user_id", type="int", default=None, help="required HumanUser id when using '--list = tasks'")
    parser.add_option("-C", "--create_version", type="string", default=None, help="create Version in Shotgun. Value must be a valid JSON encoded hash with required keys")
    parser.add_option("-U", "--update_version", type="string", default=None, help="update Version in Shotgun. Value must be a valid JSON encoded hash with at least the id key (of the Version to update)")
    parser.add_option("-f", "--fields", action="store_true", dest="fields", help="return a list of valid fields and field types on the Version entity for storing information.")
    parser.add_option("-t", "--statuses", action="store_true", dest="statuses", help="return a list of valid status values for Versions")
    parser.add_option("-T", "--timer", action="store_true", dest="show_timer", help="show the non-scientific timing of things")
 
    (options, args) = parser.parse_args()

    #DEBUG hard-coding the auth info so we don't have to provide it while we're testing
    options.shotgun_url = "https://rush.shotgunstudio.com"
    options.shotgun_script = "rush"
    options.shotgun_key = "6b9b9fd56e8b6ce34bdb35db52f18c983bc536c8"

    # check minimum options for connecting to Shotgun
    if options.shotgun_url == None:
        bail("Missing Shotgun URL (--shotgun_url) must be specified.")
    if options.shotgun_script == None:
        bail("Missing Shotgun Script Name (--shotgun_script) must be specified.")
    if options.shotgun_key == None:
        bail("Missing Shotgun Application Key (--shotgun_key) must be specified.")
    
    # list entities
    if options.list:
        validate_list_option(options.list)
        io = ShotgunIO(options.shotgun_url, options.shotgun_script, options.shotgun_key)
        if options.list == 'version_name_templates':
            print io.listVersionNameTemplates()
        elif entity_config[options.list]['project_required'] and \
            options.project_id == None:
            bail("-l (--list) option '%s' requires a project id: -p (--project_id)" % options.list)
        elif options.list in ['tasks'] and options.user_id == None:
            bail("-l (--list) option '%s' requires a user id: -u (--user_id)" % options.list)
        else:
            entities = io.listEntities(options.list, project_id=options.project_id, user_id=options.user_id)
            print entities

    # list fields
    elif options.fields:
        io = ShotgunIO(options.shotgun_url, options.shotgun_script, options.shotgun_key)
        fields = io.listVersionFields()
        pprint.pprint(fields)

    # list valid status values
    elif options.statuses:
        io = ShotgunIO(options.shotgun_url, options.shotgun_script, options.shotgun_key)
        statuses = io.listVersionStatusValues()
        statuses = formatRushEntities("statuses", statuses)
        print statuses

    # create Version in Shotgun with provided fields/values
    elif options.create_version:
        io = ShotgunIO(options.shotgun_url, options.shotgun_script, options.shotgun_key)
        version = io.createVersion(options.create_version)
        print version['id']
        # pprint.pprint(version)

    # update Version in Shotgun with provided fields/values
    elif options.update_version:
        io = ShotgunIO(options.shotgun_url, options.shotgun_script, options.shotgun_key)
        version = io.updateVersion(options.update_version)
        print version['id']

    else:
        bail("invalid option combination '%s'. Yeah... this error sucks right now but this is just a placeholder... we'll make it better." % sys.argv)
    
    timer['end'] = time.time()
    

    if options.show_timer:
        print "%.4f secs: connect to shotgun" % (timer['connect_end']-timer['connect_start'])
        print "%.4f secs: run query" % (timer['listEntities_end']-timer['listEntities_start'])
        print "%.4f secs: reformat output" % (timer['reformat_rush_end']-timer['reformat_rush_start'])
        print "%.4f SECS: TOTAL" % (timer['end']-timer['start'])
    sys.exit(0)

    
    


#!/usr/bin/env python

# ./shotgun_io.py -C "{\"user\":\"32 kp\",\"task\":\"2,4,Shot,2 Demo Project | Shot 1 | Match Move\",\"name\":\"Demo Project Shot_1 Match Move kp\",\"description\":\"fixing penetration for blah.\n- this was done\n- this still needs work\n-b lah\",\"job_id\":\"contrail.123\", \"job_status\":\"0\"}"
# ./shotgun_io.py -U "{\"version_id\":\"5\",\"first_frame\":\"1\",\"last_frame\":\"100\",\"frame_range\":\"1-50 61-70,2 80 90 100\",\"frame_count\":\"58\",\"frames_path\":\"/path/to/frames/image.#.jpg\",\"movie_path\":\"/path/to/movie/popcorn.mov\",\"job_id\":\"contrail.123\", \"job_status\":\"1\"}"
# ./shotgun_io.py -C "{\"user\":\"55 kp\",\"task\":\"557,65,Shot,860 Demo Animation Project | bunny_010_0010 | Anm\",\"name\":\"Demo Project bunny_010_0010 Anm kp\",\"description\":\"testing new input/output classes.\n- this was done\n- this still needs work\n-b lah\",\"job_id\":\"fakejobby 101\", \"job_status\":\"0\"}"
# ./shotgun_io.py -U "{\"version_id\":\"6074\", \"job_status\":\"1\"}

import sys
import os
import socket
import pprint
import optparse
import ConfigParser
import logging
import re
import io_input
import io_output

# setup logging
log_format = "%(filename)s %(levelname)s: %(message)s"
logging.basicConfig(format=log_format, level=logging.DEBUG)

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        python_version = "%d.%d.%d" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
        msg = "No supported JSON module is installed. It's a standard module as of Python 2.6. If you are " \
                "running an earlier version of Python (yours is v%s), you can download and install the "\
                "simplejson module from http://pypi.python.org/pypi/simplejson. If you have a package "\
                "manager on your system you can use something like `apt-get install python-simplejson` "\
                "or if you have the setuptools module installed in Python, just type `easy_install simplejson`" % python_version
        push_error(msg)

try:
    import shotgun_api3
except ImportError:
    msg = "The Shotgun API is not installed. To install it, download the latest version from "\
            "https://github.com/shotgunsoftware/python-api/downloads, extract the package and place the "\
            "shotgun_api3.py file in this directory or somewhere in your PYTHONPATH (more info on where to "\
            "install modules at http://docs.python.org/tutorial/modules.html#the-module-search-path)"
    push_error(msg)


# don't hang things up for more than 10 seconds if we can't reach Shotgun
socket.setdefaulttimeout(10)

# ====================================
# CONSTANTS (don't change these)
# not used currently but may be?
# ====================================
VERSION_STATUS_SUBMITTED = 0
VERSION_STATUS_IP = 1
VERSION_STATUS_COMPLETE = 2
VERSION_STATUS_FAILED = 3

# ====================================
# DEFAULT QUERY SETTINGS FOR RETURNING VALUES FOR SUBMIT MENUS
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
        'filters': [['sg_status_list','is','ip']],
        'fields': ['id','content','entity','project'],
        'order': [
            {'field_name':'project','direction':'asc'},{'field_name':'entity','direction':'asc'},
            {'field_name':'content','direction':'asc'}],
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

# minimum fields required to create a Version in Shotgun. 
required_sg_version_fields = ['code','project','user']


# ====================================
# END VARIABLES 
# ====================================
        
    
class ShotgunIO (object):
    def __init__(self, config): 
        
        self._config = config
        
        self.shotgun_url = config.get('shotgun', 'url')
        self.shotgun_script = config.get('shotgun', 'script_name')
        self.shotgun_key = config.get('shotgun', 'application_key')
        self._sg = None

        
        self.version_numbering = config.get('version_values', 'version_numbering')
        self.version_number_format = config.get('version_values', 'version_number_format')
        
        self.input = io_input.InputCmdLine(self._config)
        self.output = io_output.OutputDefault()
        
    def _shotgun_connect(self):
        """
        Instantiate Shotgun class for connecting to the Shotgun server
        """
        try:
            self._sg = shotgun_api3.Shotgun(self.shotgun_url, self.shotgun_script, self.shotgun_key)
        except Exception, e:
            push_error("Unable to connect to Shotgun: %s" % e)
        else:
            return True


    def validate_user(self, username):
        """
        Checks if given username string is a valid active user in Shotgun. 

        If the username is active and valid, return the id of the HumanUser entity in Shotgun.
        If the username is invalid, return None.
        
        """
        if not self._sg:
            self._shotgun_connect()
        try:
            user = self._sg.find_one('HumanUser', [['login','is',username],['sg_status_list','is','act']], ['id','login'])
        except Exception, e:
            push_error("Error validating user in Shotgun: %s" % (e))
        out = self.output.format_output('user', user)

        return out
                

    def list_version_fields(self):
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
            push_error("Error retrieving list of Version fields from Shotgun: %s" % (e))
        
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


    def list_version_status_values(self):
        """
        Returns a list of valid status values for the Version Status field
        
        """
        if not self._sg:
            self._shotgun_connect()
        try:
            status_field = self._sg.schema_field_read('Version','sg_status_list')
        except Exception, e:
            push_error("Error retrieving list of valid status values for Versions from Shotgun: %s" % (e))
        
        out = self.output.format_output('version_statuses', status_field['sg_status_list']['properties']['valid_values']['value'])

        return out


    def list_version_name_templates(self):
        """Return a list of the defined Version name templates

        The first entry in the list is the default. If the first
        entry is blank, then there is no default set.

        Allows tokens like ${project} or ${shot} that can be used
        for string replacement based on choices in the submit tool. 
        """
        template_list = []
        template_list = self._config.get('version_values','version_name_templates').split(',')

        out = self.output.format_output('version_name_templates', template_list)

        return out
         

    def list_entities(self, entity_type, **kwargs):
        """
        Retrieve a list of entities from Shotgun
        """
        entities = []

        # special cases: combine two calls and return combo
        if entity_type == "assetsandshots":
            kwargs['no_format'] = True
            for t in ['shots','assets']:
                entities += self.list_entities(t, **kwargs)
        
        elif entity_type == "projectsandtasks":
            kwargs['no_format'] = True
            for t in ['projects','tasks']:
                entities += self.list_entities(t, **kwargs)
        
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
                entities = self._sg.find(entity_config[entity_type]['entity_type'], filters=filters, 
                            fields=entity_config[entity_type]['fields'], order=entity_config[entity_type]['order'])
            except Exception, e:
                push_error("Error retrieving %s list from Shotgun: %s" % (entity_type, e))
            else:
                # in a recursive call to combine entity lookups so we'll do the
                # formatting at the end of it
                if 'no_format' in kwargs and kwargs['no_format']:
                    return entities
                
        out = self.output.format_output(entity_type, entities)

        return out


    def parse_scene_path_for_project_and_shot(self, scenepath):
        """
        Attemps to match a Project and Shot name automatically from the scene file
        path based on regex definitions in the shotgun_io config
        """
        for r in self.scenefile_path_regexes:
            result = re.match(r, scenepath)
            if result:
                project, shot = result.groups()
                if project and shot:
                    return (project,shot)
                else:
                    return None


    def get_next_version_number(self):
        """
        Attempts to find the next Version number for this Shot

        Logic depends on what the setting for self.version_numbering is
        """
        next_number = 1
        task = None
        step = None
        task_field = self._config.get('version_fields', 'project')

        if not self._sg:
            self._shotgun_connect()

        filters = [['entity', 'is', self.input.shotgun_input['entity']]]        
        
        if self.version_numbering == 'task':
            if task_field in self.input.shotgun_input:
                task = self.input.shotgun_input[task_field]
            filters.append([task_field, 'is', task])
        
        elif self.version_numbering == 'pipeline_step':
            # lookup pipeline step for provided task
            if task_field in self.input.shotgun_input:
                result = self._sg.find_one('Task', [['id', 'is', self.input.shotgun_input[task_field]]], ['step'])
                if result:
                    step = result['step']                    
            filters.append(['%s.Task.step' % task_field, 'is', step])

        result = self._sg.find("Version", filters, ['code'], 
                    order=[{'field_name':'content','direction':'asc'}])
        
        for v in result:
            match = re.search('v(\d*$)',v['code'])
            if match and len(match.groups())==1:
                version_number = int(match.group(1))
                if version_number >= next_number:
                    next_number = version_number+1

        return next_number


    def _decode_version_hash(self, version_data):
        """
        convert JSON string representation of Version into Python object.
        """        
        fp = None
        # input is stdin
        if version_data == "-":
            version_data = "$STDIN" # for error messages
            fp = sys.stdin
        # input is file
        elif os.path.isfile(version_data):
            try:
                fp = open(version_data)
            except IOError, e:
                push_error("unable to open input file %s: %s" % (os.path.abspath(version_data), e))
        if fp:    
            try:
                self.input.raw_input = json.load(fp)
            except ValueError, e:
                push_error("invalid JSON format in file %s: %s" % (os.path.abspath(version_data), e))
        else:
            # input was provided as an argument
            try:
                self.input.raw_input = json.loads(version_data)
            except ValueError, e:
                push_error("invalid JSON format provided as argument: %s" % e)


    def create_version(self, version_hash):
        """
        create new Version entity in Shotgun from the provided JSON-encoded Version data

        performs JSON decoding, validation, and data translation to the expected Shotgun format
        based on the integration environment.
        """
        # turn JSON string into valid dictionary hash
        self._decode_version_hash(version_hash)
        self.input.extract_version_data()

        # check required fields (sometimes project and shot will be part of the task need to handle that)
        for f in required_sg_version_fields:
            if not f in self.input.shotgun_input:
                push_error("Unable to create Version in Shotgun. Missing required Shotgun field '%s'" % f)

        # append next version number formatted as defined
        self.input.shotgun_input['code'] += self.version_number_format % self.get_next_version_number()
        print self.input.shotgun_input

        # create version
        if not self._sg:
            self._shotgun_connect()
        try:
            version = self._sg.create('Version', self.input.shotgun_input)
        except Exception, e:
            push_error("Error creating Version in Shotgun: %s" % e)
        
        return version


    def update_version(self, version_hash):
        """
        Update existing Version entity in Shotgun with the provided JSON-encoded Version data

        performs JSON decoding, validation, and data translation to the expected Shotgun format
        based on the integration environment. Requires 'id' key with integer value that corresponds
        to the id of the Version entity to update in Shotgun.
        """
        # turn JSON string into valid dictionary hash
        self._decode_version_hash(version_hash)
        self.input.extract_version_data()

        # check required fields
        if 'id' not in self.input.shotgun_input:
            push_error("Unable to update Version in Shotgun. Missing required field 'version_id' in Version hash")
        
        # extract Version id and remove it from the dict
        version_id = self.input.shotgun_input['id']
        del(self.input.shotgun_input['id'])

        # update version
        if not self._sg:
            self._shotgun_connect()
        try:
            version = self._sg.update('Version', version_id, self.input.shotgun_input)
        except Exception, e:
            push_error("Error updating Version in Shotgun: %s" % e)
        
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




def readConfig():
    # Read/parse the config
    config = ConfigParser.ConfigParser()
    paths = [os.path.abspath( os.path.dirname(sys.argv[0]) ) + "/shotgun_io.conf", '/etc/shotgun_io.conf']
    for path in paths:
        if os.path.exists(path):
            config.read(path)
            return config
    raise ValueError('shotgun_io.conf config file not found. Searched %s' % (paths))


def push_error(errmsg='', cont=False):
    logging.error(errmsg)
    if not cont:
        sys.exit(1)


def validate_list_option(option):
    non_entity_options = ['version_name_templates']
    if option in entity_config.keys() or option in non_entity_options:
        return True
    else:
        push_error("-l (--list) option must be a valid option:\n%s" % (entity_config.keys()+non_entity_options))


if __name__ == '__main__':

    # options  
    ##TODO: do more robust error checking for mutually exclusive options
    usage = "usage: %prog [options]"
    parser = ShotgunIoOptionParser(usage=usage)
    parser.add_option("-l", "--list", type="string", default=None, help="retrieve a list of entities from Shotgun")
    parser.add_option("-p", "--project_id", type="int", default=None, help="required Project id when using '--list assets', or '--list shots'")
    parser.add_option("-u", "--user_id", type="int", default=None, help="required HumanUser id when using '--list = tasks'")
    parser.add_option("-n", "--user_name", type="string", default=None, help="test whether provided username is valid")
    parser.add_option("-C", "--create_version", type="string", default=None, help="create Version in Shotgun. Value must be a valid JSON encoded hash with required keys")
    parser.add_option("-U", "--update_version", type="string", default=None, help="update Version in Shotgun. Value must be a valid JSON encoded hash with at least the id key (of the Version to update)")
    parser.add_option("-f", "--fields", action="store_true", dest="fields", help="return a list of valid fields and field types on the Version entity for storing information.")
    parser.add_option("-t", "--statuses", action="store_true", dest="statuses", help="return a list of valid status values for Versions")
  
    (options, args) = parser.parse_args()
    config = readConfig()

    # list entities
    if options.list:
        validate_list_option(options.list)
        io = ShotgunIO(config)
        if options.list == 'version_name_templates':
            print io.list_version_name_templates()
        elif entity_config[options.list]['project_required'] and \
            options.project_id == None:
            push_error("-l (--list) option '%s' requires a project id: -p (--project_id)" % options.list)
        elif options.list in ['tasks'] and options.user_id == None:
            push_error("-l (--list) option '%s' requires a user id: -u (--user_id)" % options.list)
        else:
            entities = io.list_entities(options.list, project_id=options.project_id, user_id=options.user_id)
            print entities

    # validate username
    elif options.user_name:
        io = ShotgunIO(config)
        user_id = io.validate_user(options.user_name)
        print user_id

    # list fields
    elif options.fields:
        io = ShotgunIO(config)
        fields = io.list_version_fields()
        print fields

    # list valid status values
    elif options.statuses:
        io = ShotgunIO(config)
        statuses = io.list_version_status_values()
        print statuses

    # create Version in Shotgun
    elif options.create_version:
        io = ShotgunIO(config)
        version = io.create_version(options.create_version)
        print version['id']

    # update Version in Shotgun
    elif options.update_version:
        io = ShotgunIO(config)
        version = io.update_version(options.update_version)
        print version['id']

    else:
        print parser.usage
        push_error("invalid option combination '%s'. Yeah... this error sucks right now but this is just a placeholder... we'll make it better." % sys.argv)
    
    sys.exit(0)

    
    


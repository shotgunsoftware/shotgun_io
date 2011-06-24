#!/usr/bin/env python

# ./shotgun_io.py -C "{\"user\":\"32 kp\",\"task\":\"2,4,Shot,2 Demo Project | Shot 1 | Match Move\",\"name\":\"Demo Project Shot_1 Match Move kp\",\"description\":\"fixing penetration for blah.\n- this was done\n- this still needs work\n-b lah\",\"job_id\":\"contrail.123\", \"job_status\":\"0\"}"
# ./shotgun_io.py -U "{\"version_id\":\"5\",\"first_frame\":\"1\",\"last_frame\":\"100\",\"frame_range\":\"1-50 61-70,2 80 90 100\",\"frame_count\":\"58\",\"frames_path\":\"/path/to/frames/image.#.jpg\",\"movie_path\":\"/path/to/movie/popcorn.mov\",\"job_id\":\"contrail.123\", \"job_status\":\"1\"}"
# ./shotgun_io.py -C "{\"user\":\"55 kp\",\"task\":\"557,65,Shot,860 Demo Animation Project | bunny_010_0010 | Anm\",\"name\":\"Demo Project bunny_010_0010 Anm kp\",\"description\":\"testing new input/output classes.\n- this was done\n- this still needs work\n-b lah\",\"job_id\":\"fakejobby 101\", \"job_status\":0}"
# ./shotgun_io.py -U "{\"version_id\":6074, \"job_status\":1}
# ./shotgun_io.py -U "{\"version_id\":6084, \"job_status\":2, \"thumbnail\":\"/Users/kp/foobar.jpg/\"}

import sys
import os
import socket
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
    import shotgun_api3
except ImportError:
    msg = "The Shotgun API is not installed. To install it, download the latest version from "\
            "https://github.com/shotgunsoftware/python-api/downloads, extract the package and place the "\
            "shotgun_api3.py file in this directory or somewhere in your PYTHONPATH (more info on where to "\
            "install modules at http://docs.python.org/tutorial/modules.html#the-module-search-path)"
    logging.error(msg)
    sys.exit(1)


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


# minimum fields required to create a Version in Shotgun. 
required_sg_version_fields = ['code','project','user']


# ====================================
# END VARIABLES 
# ====================================

class ShotgunIO(object):
    """
    Factory for ShotgunIO instance.

    Returns ShotgunIOBase instance by default.
    If a 'custom_module' is defined in shotgun_io.conf, attempts to import the specified
    file and instantiate the ShotgunIOCustom class instead.
    """
    def __new__(klass, commandline=False, **kwargs):
        # load config and check if a custom module is enabled
        config = ShotgunIO.load_config()
        custom_module_str = config.get('shotgun_io', 'custom_module')

        # if no custom module is defined return the base class instance
        if not custom_module_str:
            return ShotgunIOBase(config, commandline)
        else:
            # attempt to load the custom module if enabled and return custom instance
            try:
                custom_module = __import__(custom_module_str)
            except ImportError:
                logging.warning("custom module '%s' specified in config, but was not found. "\
                "Using the default ShotgunIO class instead.")
                return ShotgunIOBase(config, commandline)
            else:
                return custom_module.ShotgunIOCustom(config, commandline)
    
    
    @staticmethod
    def load_config():
        """
        Reads the configuration settings from the shotgun_io.conf file
        """
        # Read/parse the config
        config = ShotgunConfigParser()
        paths = [os.path.abspath( os.path.dirname(__file__) ) + "/shotgun_io.conf", '/etc/shotgun_io.conf']
        for path in paths:
            if os.path.exists(path):
                config.read(path)
                return config
        raise ValueError('shotgun_io.conf config file not found. Searched %s' % (paths))





class ShotgunIOBase(object):
    def __init__(self, config, commandline): 
        
        self._config = config

        # shotgun server info
        self.shotgun_url = self._config.get('shotgun', 'url')
        self.shotgun_script = self._config.get('shotgun', 'script_name')
        self.shotgun_key = self._config.get('shotgun', 'application_key')
        self._sg = None

        self.commandline = commandline

        # query-related settings (filters, ordering, etc.)
        self.entity_query_config = self._entity_query_settings()
        
        # version numbering
        self.version_numbering = self._config.get('version_values', 'version_numbering')
        self.version_number_format = self._config.get('version_values', 'version_number_format')
        
        # scenefile regexes
        self.scenefile_path_regexes = self._config.getlist('version_values', 'scenefile_path_regexes')

        # input and output validation and formatting
        self.input = io_input.InputDefault(self._config) 
        if self.commandline:
            self.output = io_output.OutputCmdLine()
        else:
            self.output = io_output.OutputDefault()


    def _shotgun_connect(self):
        """
        Instantiate Shotgun class for connecting to the Shotgun server.

        If connection already exists, no action is taken.

        @@TODO test this with the Shotgun JSON API.  
        """
        if self._sg:
            return True
        
        try:
            self._sg = shotgun_api3.Shotgun(self.shotgun_url, self.shotgun_script, self.shotgun_key)
        except Exception, e:
            logging.error("Unable to connect to Shotgun: %s" % e)
        else:
            return True

    
    def _entity_query_settings(self):
        """
        Dictionary defining default query settings for Shotgun.

        May be overridden by re-defining the dictionary.
        """
        entity_query_config = {
            'users': {
                'entity_type': 'HumanUser',
                'filters': [['sg_status_list', 'is_not', 'dis']],
                'fields': ['id','login'],
                'order': [{'field_name':'login','direction':'asc'}],
                'project_required': False,
                'user_required': False,
               },
            'projects': {
                'entity_type': 'Project',
                'filters': [['sg_status', 'is_not', 'Archive'],['name', 'is_not', 'Template Project']],
                'fields': ['id','name'],
                'order': [{'field_name':'name','direction':'asc'}],
                'project_required': False,
                'user_required': False,
                },
            'assets': {
                'entity_type': 'Asset',
                'filters': [['sg_status_list', 'is_not', 'omt']],
                'fields': ['id','code'],
                'order': [{'field_name':'code','direction':'asc'}],
                'project_required': True,
                'user_required': False,
                },
            'shots': {
                'entity_type': 'Shot',
                'filters': [['sg_status_list', 'is_not', 'omt']],
                'fields': ['id','code'],
                'order': [{'field_name':'code','direction':'asc'}],
                'project_required': True,
                 'user_required': False,
               },
            'tasks': {
                'entity_type': 'Task',
                'filters': [['sg_status_list','is','ip']],
                'fields': ['id','content','entity','project'],
                'order': [
                    {'field_name':'project','direction':'asc'},{'field_name':'entity','direction':'asc'},
                    {'field_name':'content','direction':'asc'}],
                'project_required': False,
                'user_required': True,
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
        return entity_query_config


    def _validate_list_option(self, option):
        """
        Validate the value provided when specifying the -l option on the command-line
        """
        non_entity_options = ['version_name_templates']
        if option in self.entity_query_config.keys() or option in non_entity_options:
            return True
        else:
            if self.commandline:
                logging.error("-l (--list) option must be a valid option:\n%s" % (self.entity_query_config.keys()))
                sys.exit(1)
            else:
                return False


    def validate_user(self, username):
        """
        Checks if given username string is a valid active user in Shotgun. 

        If the username is active and valid, returns the id of the HumanUser entity in Shotgun.
        If the username is invalid, returns None.
        """
        self._shotgun_connect()
        try:
            user = self._sg.find_one('HumanUser', [['login','is',username],['sg_status_list','is','act']], ['id','login'])
        except Exception, e:
            logging.error("Error validating user in Shotgun: %s" % (e))
        out = self.output.format_output('user', user)

        return out
                

    def list_version_fields(self):
        """
        Returns a dict of editable Version fields categorized by field type. 

        The key is the string field type and the value is a list of string field
        names. Internal and non-editable fields are filtered out automatically.
        
        @@TODO: The filtering could be more intelligent.
        """
        self._shotgun_connect()
        sorted_fields = {}

        try:
            fields = self._sg.schema_field_read('Version')
        except Exception, e:
            logging.error("Error retrieving list of Version fields from Shotgun: %s" % (e))
        
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
        self._shotgun_connect()
        try:
            status_field = self._sg.schema_field_read('Version','sg_status_list')
        except Exception, e:
            logging.error("Error retrieving list of valid status values for Versions from Shotgun: %s" % (e))
        
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
        if not self._validate_list_option(entity_type):
            raise ValueError("entity_type value '%s' is invalid. Valid options are %s"\
                % (entity_type, self.entity_query_config.keys()))
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
            filters = self.entity_query_config[entity_type]['filters']
            # check if we need to inject project or user filters
            if self.entity_query_config[entity_type]['project_required']:
                if not 'project_id' in kwargs or not kwargs['project_id']:
                    raise ValueError("'project_id' is a required parameter for listing '%s'" % entity_type)
                filters.append(['project', 'is', {'type':'Project', 'id': kwargs['project_id']}])
            if self.entity_query_config[entity_type]['user_required']:
                if not 'user_id' in kwargs or not kwargs['user_id']:
                    raise ValueError("'user_id' is a required parameter for listing '%s'" % entity_type)
                if entity_type == 'tasks':
                    filters.append(['task_assignees', 'is', {'type':'HumanUser', 'id': kwargs['user_id']}])
                elif entity_type == 'projects':
                    # we could add a filter for Projects the user is linked to but
                    # if this is overridden by permissions, we have no way of knowing that 
                    # from the API. So when we do, add that logic here.
                    pass

            self._shotgun_connect()
            try:
                entities = self._sg.find(self.entity_query_config[entity_type]['entity_type'], filters=filters, 
                            fields=self.entity_query_config[entity_type]['fields'], order=self.entity_query_config[entity_type]['order'])
            except Exception, e:
                logging.error("Error retrieving %s list from Shotgun: %s" % (entity_type, e))
            else:
                # in a recursive call to combine entity lookups we'll do the
                # formatting when we're all done
                if 'no_format' in kwargs and kwargs['no_format']:
                    return entities
                
        out = self.output.format_output(entity_type, entities)

        return out


    def parse_scene_path_for_project_and_shot(self, scenepath):
        """
        Attemps to match a Project and Shot name automatically from the scene file
        path based on regex definitions in the shotgun_io config.

        Good candidate for overriding in ShotgunIOCustom since there's
        often varying logic that needs to be implemented for each studio.

        Currently just returns strings for project and shot which can then
        be used to lookup their entity ids in Shotgun.
        Returns None if no match was found.
        """
        ret = None
        for r in self.scenefile_path_regexes:
            result = re.match(r, scenepath)
            if result:
                project, shot = result.groups()
                if project and shot:
                    ret = (project, shot)

        out = self.output.format_output('scenepath_parse', ret)

        return out
        

    def get_next_version_number(self):
        """
        Attempts to find the next Version number for this parent entity. 

        Logic depends on what the setting for version_numbering is in the config.
        """
        self._shotgun_connect()
        next_number = 1
        task = None
        step = None
        task_field = self._config.get('version_fields', 'project')

        filters = [['entity', 'is', self.input.shotgun_input['entity']]]        
        
        # task-based numbering: add task filter
        if self.version_numbering == 'task':
            if task_field in self.input.shotgun_input:
                task = self.input.shotgun_input[task_field]
            filters.append([task_field, 'is', task])
        
        # pipeline step-based numbering: add step filter
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


    def create_version(self, version_hash):
        """
        create new Version entity in Shotgun from the provided JSON-encoded Version data

        performs JSON decoding, validation, and data translation to the expected Shotgun format
        based on the integration environment.
        """
        ret = {}
        # turn JSON string into valid dictionary hash
        # self._decode_version_hash(version_hash)
        self.input.extract_version_data(version_hash)

        # check required fields (sometimes project and shot will be part of the task need to handle that)
        for f in required_sg_version_fields:
            if not f in self.input.shotgun_input:
                logging.error("Unable to create Version in Shotgun. Missing required Shotgun field '%s'" % f)

        # append next version number formatted as defined
        if self.version_numbering:
            self.input.shotgun_input['code'] += self.version_number_format % self.get_next_version_number()

        # check if 'thumbnail' is in the dictionary, extract and save for after we create the version
        if 'thumbnail' in self.input.shotgun_input:
            thumbnail = self.input.shotgun_input['thumbnail']
            del(self.input.shotgun_input['thumbnail'])
        
        # create version
        self._shotgun_connect()
        try:
            version = self._sg.create('Version', self.input.shotgun_input)
            ret.update(version)
        except Exception, e:
            logging.error("Error creating Version in Shotgun: %s" % e)
        else:
            if thumbnail:
                result = self.upload_thumbnail(version['id'], thumbnail)
                if result:
                    ret['thumbnail_id'] = result

        return ret


    def update_version(self, version_hash):
        """
        Update existing Version entity in Shotgun with the provided JSON-encoded Version data

        performs JSON decoding, validation, and data translation to the expected Shotgun format
        based on the integration environment. Requires 'id' key with integer value that corresponds
        to the id of the Version entity to update in Shotgun.
        """
        ret = {}

        # turn JSON string into valid dictionary hash
        # self._decode_version_hash(version_hash)
        self.input.extract_version_data(version_hash)

        # check required fields
        if 'id' not in self.input.shotgun_input:
            logging.error("Unable to update Version in Shotgun. Missing required field 'version_id' in Version hash")
        
        # extract Version id and remove it from the dict
        version_id = self.input.shotgun_input['id']
        del(self.input.shotgun_input['id'])

        # check if 'thumbnail' is in the dictionary, upload thumbnail
        if 'thumbnail' in self.input.shotgun_input:
            result = self.upload_thumbnail(version_id, self.input.shotgun_input['thumbnail'])
            if result:
                ret['thumbnail_id'] = result
            del(self.input.shotgun_input['thumbnail'])

        # check if we have anything to update
        if len(self.input.shotgun_input) == 0:
            return ret

        # update version
        self._shotgun_connect()
        try:
            version = self._sg.update('Version', version_id, self.input.shotgun_input)
            ret.update(version)
        except Exception, e:
            logging.error("Error updating Version in Shotgun: %s" % e)
        
        return ret


    def upload_thumbnail(self, version_id, thumb_path):
        """
        Upload file located at thumb_path as thumbnail for Version with version_id
        """
        self._shotgun_connect()
        # check that thumb_path exists and is readable.
        if not os.path.exists(thumb_path):
            logging.error("Error uploading thumbnail '%s' to Shotgun for Version %d: thumbnail path not found." % (thumb_path, version_id))
            return False

        # upload thumbnail
        try: 
            result = self._sg.upload_thumbnail('Version', version_id, thumb_path)
        except Exception, e:
            logging.error("Error uploading thumbnail '%s' to Shotgun for Version %d: %s" % (thumb_path, version_id, e))
            return False

        return self.output.format_output("thumbnail_id", result)






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


class ShotgunConfigParser(ConfigParser.ConfigParser):
    # def __init__(self):
    #     super(ShotgunConfigParser, self).__init__()

    def getlist(self, section, option, sep=",", chars=None):
        """
        Return a list from a ConfigParser option. By default, split on a comma and strip whitespaces.
        """
        
        return [ chunk.strip(chars) for chunk in self.get(section,option).split(sep) ]




def read_options():
    """
    reads options when shotgun_io is called from the commandline
    """
    # options  
    ##TODO: do more robust error checking for mutually exclusive options
    usage = "USAGE: %s [options]" % os.path.basename(__file__)
    parser = ShotgunIoOptionParser(usage=usage)
    parser.add_option("-l", "--list", type="string", default=None, help="retrieve a list of entities from Shotgun")
    parser.add_option("-p", "--project_id", type="int", default=None, help="required Project id when using '--list assets', or '--list shots'")
    parser.add_option("-u", "--user_id", type="int", default=None, help="required HumanUser id when using '--list = tasks'")
    parser.add_option("-n", "--user_name", type="string", default=None, help="test whether provided username is valid")
    parser.add_option("-C", "--create_version", type="string", default=None, help="create Version in Shotgun. Value must be a valid JSON encoded hash with required keys")
    parser.add_option("-U", "--update_version", type="string", default=None, help="update Version in Shotgun. Value must be a valid JSON encoded hash with at least the id key (of the Version to update)")
    parser.add_option("-f", "--fields", action="store_true", dest="fields", help="return a list of valid fields and field types on the Version entity for storing information.")
    parser.add_option("-t", "--statuses", action="store_true", dest="statuses", help="return a list of valid status values for Versions")
    parser.add_option("-x", "--logfiles", type="string", default=None, help="path to logfiles for processing (if implemented)")
    parser.add_option("-m", "--templates", action="store_true", dest="templates", help="return a list of Version name templates defined in the config")
    parser.add_option("-r", "--parse_scenefile_path", type="string", default=None, help="return project and shot parsed from scenefile path based on regex patterns defined in config.")
  
    return parser


def main():
    """
    Handles execution of shotgun_io when called from the command line
    """

    parser = read_options()
    (options, args) = parser.parse_args()
    
    io = ShotgunIO(True)
   
    # list entities
    if options.list:
        io._validate_list_option(options.list)
        if io.entity_query_config[options.list]['project_required'] and \
            options.project_id == None:
            logging.error("-l (--list) option '%s' requires a project id: -p (--project_id)" % options.list)

        elif options.list in ['tasks'] and options.user_id == None:
            logging.error("-l (--list) option '%s' requires a user id: -u (--user_id)" % options.list)

        else:
            print io.list_entities(options.list, project_id=options.project_id, user_id=options.user_id)
            
    # validate username
    elif options.user_name:
        print io.validate_user(options.user_name)

    # list fields
    elif options.fields:
        print io.list_version_fields()

    # list valid status values
    elif options.statuses:
        print io.list_version_status_values()

    # create Version in Shotgun
    elif options.create_version:
        print io.create_version(options.create_version)

    # update Version in Shotgun
    elif options.update_version:
        print io.update_version(options.update_version)

    # process logfiles
    elif options.logfiles:
        print io.process_logfiles(options.logfiles)

    # list version name templates
    elif options.templates:
        print io.list_version_name_templates()

    # parse scenefile path
    elif options.parse_scenefile_path:
        print io.parse_scene_path_for_project_and_shot(options.parse_scenefile_path)

    else:
        print parser.usage
        if len(sys.argv) > 1:
            logging.error("invalid option combination '%s'. Yeah... this error sucks right now but this is just a placeholder... we'll make it better." % sys.argv[1])
        else:
            logging.error("At least one option is required. No options specified")
            # list options here




if __name__ == '__main__':
    # executed only when called from the command line
    sys.exit(main())



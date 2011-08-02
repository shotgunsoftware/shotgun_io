#!/usr/bin/env python
import os
import sys
import re
import logging
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
        raise ImportError(msg)



class InputDefault(object):
    def __init__(self, config): 
        self._config = config
        self._valid_version_keys = [
            'name', 'description', 'user', 'project', 'task', 'shot', 
            'first_frame', 'last_frame', 'frame_count', 'frame_range', 
            'job_status', 'total_render_time', 'avg_frame_time', 'version_id', 
            'thumbnail', 'movie_path', 'frames_path', 'job_id'
            ]
        self._version_schema = None

        self.version_statuses = [
            config.get('version_values', 'status_submitted'), 
            config.get('version_values', 'status_ip'), 
            config.get('version_values', 'status_complete'), 
            config.get('version_values', 'status_failed')
        ]
        self.version_name_force_lowercase = config.get('version_values', 'version_name_force_lowercase')
        self.version_name_replace_spaces = config.get('version_values', 'version_name_replace_spaces')
        self.version_name_space_token = config.get('version_values', 'version_name_space_token')

        self.raw_input = None
        self.shotgun_input = {}
        self.thumbnail_path = None
        self.movie_upload = None
        self.action = None     

        for attr in self._valid_version_keys:
            setattr(self, attr, None)        
        self.name = None

    def _is_url_field(self, field_name):
        if field_name in self._version_schema:
            if self._version_schema[field_name]['data_type']['value'] == 'url':
                return True
        return False
        


    def _input_format_name(self, value):
        try:
            v = value.strip()
        except AttributeError:
            raise ValueError("Input data for 'version_name' must be a non-empty string. (provided value: %s)" % (value))
        else:
            if v == '':
                raise ValueError("Input data for 'version_name' must be a non-empty string. (provided value: %s)" % (value))       
        self._shotgun_format_name(value) 


    def _input_format_description(self, value):
        try:
            v = value.strip()
        except AttributeError:
            raise ValueError("Input data for 'description' must be a string. (provided value: %s)" % (value))
        self._shotgun_format_description(v) 


    # @@TODO allow for local file links.
    def _input_format_frames_path(self, value):
        try:
            v = value.strip()
        except AttributeError:
            raise ValueError("Input data for 'frames_path' must be a non-empty string. (provided value: %s)" % (value))
        else:
            if v == '':
                raise ValueError("Input data for 'frames_path' must be a non-empty string. (provided value: %s)" % (value))       
        # setting this flags thumbnail upload. ShotgunIO will determine which
        # frame it should be.
        self.thumbnail_path = value
        self._shotgun_format_frames_path(value) 


    # @@TODO document movie_upload if we use it or use of file/link fields
    def _input_format_movie_path(self, value):
        try:
            v = value.strip()
        except AttributeError:
            raise ValueError("Input data for 'movie_path' must be a non-empty string. (provided value: %s)" % (value))
        else:
            if v == '':
                raise ValueError("Input data for 'movie_path' must be a non-empty string. (provided value: %s)" % (value))       
        if self._config.get('version_fields', 'upload_movie'):
            self.movie_upload = v
        else:
            self._shotgun_format_movie_path(value) 


    def _input_format_user(self, value):
        if not isinstance(value, int):
            raise ValueError("Input data for 'user' must be an integer. (provided value: %s is a %s)" % (value, type(value)))        
        self._shotgun_format_user(value) 


    def _input_format_project(self, value):
        if not isinstance(value, int):
            raise ValueError("Input data for 'project' must be an integer. (provided value: %s is a %s)" % (value, type(value)))        
        self._shotgun_format_project(value) 


    # @@TODO if we have the Task we should get the Project and entity from it in the main script if not provided
    def _input_format_task(self, value):
        if not isinstance(value, int):
            raise ValueError("Input data for 'task' must be an integer. (provided value: %s is a %s)" % (value, type(value)))
        self._shotgun_format_task(value)
        

    def _input_format_shot(self, value):
        error_msg = "Input data for 'shot' must be an dictionary with non-empty 'type' and 'id' keys. (provided value: %s)"
        if not isinstance(value, dict):
            raise ValueError(error_msg % (value))       
        
        # get keys
        try:
            entity_type = value['type'].strip()
            entity_id = value['id']
        except (KeyError, AttributeError):
            raise ValueError(error_msg % (value))
        
        # validate entity_type
        r = re.match("^([A-Z][A-z0-9]+)$", entity_type)
        try:
            r.group(1)
        except (IndexError, AttributeError):
            raise ValueError("'type' key value for 'shot' in input data must be a valid CamelCased Shotgun entity type string (provided value: %s)" % entity_type)
        
        # validate id
        if not isinstance(entity_id, int):
            raise ValueError("'id' key value for 'shot' in input data must be an integer. (provided value: %s is a %s)" % (entity_id, type(entity_id)))        

        self._shotgun_format_shot(value)


    def _input_format_first_frame(self, value):
        if not isinstance(value, int) or value is None:
            raise ValueError("Input data for 'first_frame' must None or an integer. (provided value: %s is a %s)" % (value, type(value)))        
        self._shotgun_format_first_frame(value) 


    def _input_format_last_frame(self, value):
        if not isinstance(value, int) or value is None:
            raise ValueError("Input data for 'last_frame' must None or an integer. (provided value: %s is a %s)" % (value, type(value)))            
        self._shotgun_format_last_frame(value) 


    def _input_format_frame_count(self, value):
        if not isinstance(value, int) or value is None:
            raise ValueError("Input data for 'frame_count' must be an integer. (provided value: %s is a %s)" % (value, type(value)))            
        self._shotgun_format_frame_count(value) 


    def _input_format_frame_range(self, value):
        try:
            v = value.strip()
        except AttributeError:
            raise ValueError("Input data for 'frame_range' must be a string. (provided value: %s)" % (value))
        else:
            self._shotgun_format_frame_range(v) 


    def _input_format_job_status(self, value):
        if not isinstance(value, int) or value is None:
            raise ValueError("Input data for 'job_status' must be an integer. (provided value: %s is a %s)" % (value, type(value)))            
        if not value in range(0,4):
            raise ValueError("Input data for 'job_status' must be an integer between 0 and 3. (provided value: %s)" % (value))        
        self._shotgun_format_job_status(value) 


    def _input_format_job_id(self, value):
        try:
            v = value.strip()
        except AttributeError:
            raise ValueError("Input data for 'job_id' must be a string. (provided value: %s)" % (value))
        self._shotgun_format_job_id(v) 


    def _input_format_total_render_time(self, value):
        if not isinstance(value, int) or value is None:
            raise ValueError("Input data for 'total_render_time' must be an integer. (provided value: %s is a %s)" % (value, type(value)))            
        self._shotgun_format_total_render_time(value) 


    def _input_format_avg_frame_time(self, value):
        if not isinstance(value, int) or value is None:
            raise ValueError("Input data for 'avg_frame_time' must be an integer. (provided value: %s is a %s)" % (value, type(value)))           
        self._shotgun_format_avg_frame_time(value) 


    def _input_format_version_id(self, value):
        # can't assign a version id when creating
        if self.action == 'create':
            raise ValueError("'version_id' is read-only, you cannot assign it when creating Versions")
        if not isinstance(value, int) or value is None:
            raise ValueError("Input data for 'version_id' must be an integer. (provided value: %s is a %s)" % (value, type(value)))            
        self._shotgun_format_version_id(value) 

    
    def _input_format_thumbnail(self, value):
        try:
            file_path = value.strip()
        except AttributeError:
            raise ValueError("Input data for 'thumbnail' must be a non-empty string path to a valid file. (provided value: %s)" % (value))
        
        try:
            open(file_path)
        except IOError:
            raise ValueError("Input data for 'thumbnail' is not a valid file. (provided value: %s)" % (value))
        
        self.thumbnail_path = value


    def _shotgun_format_description(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'description') ] = value


    def _shotgun_format_user(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'user') ] = {'type':'HumanUser', 'id': value}


    def _shotgun_format_project(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'project') ] = {'type':'Project', 'id': value}


    def _shotgun_format_task(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'task') ] = {'type':'Task', 'id': value}


    def _shotgun_format_shot(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'shot') ] = value


    def _shotgun_format_first_frame(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'first_frame') ] = value


    def _shotgun_format_last_frame(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'last_frame') ] = value


    def _shotgun_format_frame_count(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'frame_count') ] = value


    def _shotgun_format_frame_range(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'frame_range') ] = value


    def _shotgun_format_job_status(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'job_status') ] = self.version_statuses[value]


    def _shotgun_format_total_render_time(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'total_render_time') ] = value


    def _shotgun_format_avg_frame_time(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'avg_frame_time') ] = value


    def _shotgun_format_frames_path(self, value):
        if self._is_url_field( self._config.get('version_fields', 'frames_path') ):
            value = { 'local_path': value }
        self.shotgun_input[ self._config.get('version_fields', 'frames_path') ] = value


    def _shotgun_format_job_id(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'job_id') ] = value


    def _shotgun_format_movie_path(self, value):
        if self._is_url_field( self._config.get('version_fields', 'movie_path') ):
            value = { 'local_path': value }
        self.shotgun_input[ self._config.get('version_fields', 'movie_path') ] = value


    def _shotgun_format_version_id(self, value):
        # id field is non-negotiable ;)
        self.shotgun_input['id'] = value

    
    def _shotgun_format_name(self, value):
        if self.version_name_replace_spaces:
            value = re.sub('\s+', self.version_name_space_token, value)
        if self.version_name_force_lowercase:
            value = value.lower()
        self.shotgun_input[ self._config.get('version_fields', 'name') ] = value

    def _validate_shotgun_input(self):
        # strip out any fields that are set in the config but are blank 
        # ick. 
        # @@todo this should be done before assigning the shotgun data  
        if '' in self.shotgun_input:
            del self.shotgun_input['']
            
        input_fields = self.shotgun_input.keys()
        for k in input_fields:
            if k not in self._version_schema:
                raise ValueError("Shotgun Version field '%s' is not valid. "\
                    "Check the version_fields section of your shotgun_io.conf "\
                    "file to ensure all of the field names are valid" % k)
       

    def extract_version_data(self, version_data):
        """
        Translation method to convert Version data provided by render queue to the common Shotgun format.

        - extracts the values
        - validates they are okay
        - converts them into Shotgun-friendly format

        Any invalid data provided will raise a ValueError. Any data keys that are provided which are not
        enabled in the config will be silently ignored

        """
        self._decode_version_hash(version_data)
        for field, value in self.raw_input.iteritems():
            if field in self._valid_version_keys:
                getattr(self, '_input_format_%s' % field)(value)
                setattr(self, field, value)

            # ignore everything else
            else:
                pass
        # strip out any fields that are set in the config but are blank   
        self._validate_shotgun_input()  
              
    def _decode_version_hash(self, version_data):
        """
        convert JSON string representation of Version into Python object.
        """               
        # if a dictionary is being passed in, no JSON decoding necessary
        if isinstance(version_data, dict):
            self.raw_input = version_data
            return

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
                logging.error("unable to open input file %s: %s" % (os.path.abspath(version_data), e))
        if fp:    
            try:
                self.raw_input = json.load(fp)
            except ValueError, e:
                logging.error("invalid JSON format in file %s: %s" % (os.path.abspath(version_data), e))
        else:
            # input was provided as an argument
            try:
                self.raw_input = json.loads(version_data)
            except ValueError, e:
                logging.error("invalid JSON format provided as argument: %s" % e)
    



class InputCmdLine(InputDefault):
    def __init__(self, config): 
        super(InputCmdLine, self).__init__(config)        


    def _input_format_name(self, value):
        if value is None or value.strip() == '':
            raise ValueError("Input data for 'version_name' must be a non-empty string. (provided value: %s)" % (value))        
        self._shotgun_format_name(value) 


    def _input_format_user(self, value):
        try:
            v = int(value.split(' ')[0])
        except ValueError:
            raise ValueError("Input data for 'user' must be an integer. (provided value: %s is a %s)" % (value, type(value)))        
        self._shotgun_format_user(v) 


    def _input_format_project(self, value):
        try:
            v = int(value.split(' ')[0])
        except ValueError:
            raise ValueError("Input data for 'project' must be an integer. (provided value: %s is a %s)" % (value, type(value)))        
        self._shotgun_format_project(v) 


    def _input_format_task(self, value):
        try:
            keys = value.split(' ')[0]
            task_id, project_id, entity_type, entity_id = keys.split(",")
        except ValueError:
            raise ValueError("Input data for 'task' must begin with 4 comma-separated values (without spaces) to represent "\
                        "TaskID,ProjectID,EntityType,EntityID. Examples:\n1,2,Shot,3\n123,45,Asset,6789 Anything else can "\
                        "follow.")
        try:
            v = int(task_id)
        except ValueError:
            raise ValueError("First comma-separated value for 'task' (task_id) must be an integer. (provided value: %s is a %s)" % (value, type(task_id)))
        else:
            self._shotgun_format_task(v)

        try:
            v = int(project_id)
        except ValueError:
            raise ValueError("Second comma-separated value for 'task' (project_id) must be an integer. (provided value: %s is a %s)" % (value, type(project_id)))
        else:
            self._shotgun_format_project(v)

        # match EntityType format
        r = re.match("^([A-Z][A-z0-9]+)$", entity_type)
        try:
            et = r.group(1)
        except (IndexError, AttributeError):
            raise ValueError("Third comma-separated value for 'task' (entity_type) must be a valid CamelCased Shotgun entity type string (provided value: %s)" % (entity_type))
        else:
            try:
                eid = int(entity_id)
            except ValueError:
                raise ValueError("Fourth comma-separated value for 'task' (entity_id) must be an integer. (provided value: %s is a %s)" % (value, type(entity_id)))
        self._shotgun_format_shot({'type':et, 'id':eid})
        

    def _input_format_shot(self, value):
        # string values need to be pattern matched still (for the advanced project/shot workflow)
        if isinstance(value, str) or isinstance(value, unicode):
            r = re.match("^([A-Z][A-z]+)/(\d+)\s*.*", value)
            try:
                value = (r.group(1), r.group(2))
            except (IndexError, AttributeError):
                raise ValueError("Input data for 'shot' must be a string that begins in the format '<EntityType>/<entity_id>' where "\
                            "EntityType is a valid CamelCased Shotgun entity type and EntityID is an integer. (provided value: %s)"\
                            "Examples:\n'Asset/123'\n'Shot/456'\n'Shot/78 100Foo Shot Awesome" % (value))
        try:
            entity_type = value[0]
            entity_id = int(value[1])
        except IndexError:
            raise ValueError("Input data for 'shot' must be an integer. (provided value: %s is a %s)" % (value, type(value)))        
        self._shotgun_format_shot(({'type':entity_type, 'id':entity_id}))


    def _input_format_first_frame(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'first_frame' must be an integer. (provided value: %s is a %s)" % (value, type(value)))        
        self._shotgun_format_first_frame(v) 


    def _input_format_last_frame(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'last_frame' must be an integer. (provided value: %s is a %s)" % (value, type(value)))            
        self._shotgun_format_last_frame(v) 


    def _input_format_frame_count(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'first_frame' must be an integer. (provided value: %s is a %s)" % (value, type(value)))            
        self._shotgun_format_frame_count(v) 


    def _input_format_job_status(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'job_status' must be an integer. (provided value: %s is a %s)" % (value, type(value)))            
            if not v in range(0,4):
                raise ValueError("Input data for 'job_status' must be an integer between 0 and 3. (provided value: %s)" % (value))        
        self._shotgun_format_job_status(v) 


    def _input_format_total_render_time(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'total_render_time' must be an integer. (provided value: %s is a %s)" % (value, type(value)))           
        self._shotgun_format_total_render_time(v) 


    def _input_format_avg_frame_time(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'avg_frame_time' must be an integer. (provided value: %s is a %s)" % (value, type(value)))           
        self._shotgun_format_avg_frame_time(v) 


    def _input_format_version_id(self, value):
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise ValueError("Input data for 'version_id' must be an integer. (provided value: %s is a %s)" % (value, type(value)))           
        self._shotgun_format_version_id(v) 


    def _validate_shotgun_input(self):
        # strip out any fields that are set in the config but are blank 
        # ick. 
        # @@todo this should be done before assigning the shotgun data  
        # @@todo log warning should have field name and correct file name 
        if '' in self.shotgun_input:
            logging.warning('ignoring field with value "%s": at least one field is not configured in shotgun_io.conf' % self.shotgun_input[''])
            del self.shotgun_input['']
            
        input_fields = self.shotgun_input.keys()
        for k in input_fields:
            if k not in self._version_schema:
                raise ValueError("Shotgun Version field '%s' is not valid. "\
                    "Check the version_fields section of your shotgun_io.conf "\
                    "file to ensure all of the field names are valid" % k)


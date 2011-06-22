#!/usr/bin/env python
import re


class InputCmdLine (object):
    def __init__(self, config): 
        self._config = config # okay to pass this in from the parent?
        
        self.version_statuses = [
            config.get('version_values', 'status_submitted'), 
            config.get('version_values', 'status_ip'), 
            config.get('version_values', 'status_complete'), 
            config.get('version_values', 'status_failed')
        ]
        self.version_name_force_lowercase = config.get('version_values', 'version_name_force_lowercase')
        self.version_name_space_token = config.get('version_values', 'version_name_replace_spaces')
        self.version_name_replace_spaces = (self.version_name_space_token is not None)

        self.raw_input = None
        self.shotgun_input = {}        


    def _input_format_name(self, value):
        if value is None or value.strip() == '':
            raise ValueError("Input data for 'version_name' must be a non-empty string. (provided value '%s')" % (value))
        
        self._shotgun_format_name(value) 


    def _input_format_user(self, value):
        try:
            v = int(value.split(' ')[0])
        except ValueError:
            raise ValueError("Input data for 'user' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
        
        self._shotgun_format_user(v) 


    def _input_format_project(self, value):
        try:
            v = int(value.split(' ')[0])
        except ValueError:
            raise ValueError("Input data for 'project' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
        
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
            raise ValueError("First comma-separated value for 'task' (task_id) must be an integer. (provided value '%s' is a %s)" % (value, type(task_id)))
        else:
            self._shotgun_format_task(v)

        try:
            v = int(project_id)
        except ValueError:
            raise ValueError("Second comma-separated value for 'task' (project_id) must be an integer. (provided value '%s' is a %s)" % (value, type(project_id)))
        else:
            self._shotgun_format_project(v)

        # match EntityType format
        r = re.match("^([A-Z][A-z0-9]+)$", entity_type)
        try:
            et = r.group(1)
        except (IndexError, AttributeError):
            raise ValueError("Third comma-separated value for 'task' (entity_type) must be a valid CamelCased Shotgun entity type string (provided value '%s')" % (entity_type))
        else:
            try:
                eid = int(entity_id)
            except ValueError:
                raise ValueError("Fourth comma-separated value for 'task' (entity_id) must be an integer. (provided value '%s' is a %s)" % (value, type(entity_id)))
            self._shotgun_format_shot((et, eid))
        

    def _input_format_shot(self, value):
        # string values need to be pattern matched still (for the advanced project/shot workflow)
        if isinstance(value, str) or isinstance(value, unicode):
            r = re.match("^([A-Z][A-z]+)/(\d+)\s+.*", value)
            try:
                value = (r.group(1), r.group(2))
            except (IndexError, AttributeError):
                raise ValueError("Input data for 'shot' must be a string that begins in the format '<EntityType>/<entity_id>' where "\
                            "EntityType is a valid CamelCased Shotgun entity type and EntityID is an integer. (provided value '%s')"\
                            "Examples:\n'Asset/123'\n'Shot/456'\n'Shot/78 100Foo Shot Awesome" % (value))
        try:
            entity_type = value[0]
            entity_id = value[1]
        except IndexError:
            raise ValueError("Input data for 'shot' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
        
        self.shotgun_input[ self._config.get('version_fields', 'shot') ] = {'type':entity_type, 'id': entity_id}
        return True


    def _input_format_first_frame(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'first_frame' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
        
        self._shotgun_format_first_frame(v) 


    def _input_format_last_frame(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'last_frame' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
            
        self._shotgun_format_last_frame(v) 


    def _input_format_frame_count(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'first_frame' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
            
        self._shotgun_format_frame_count(v) 


    def _input_format_job_status(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'job_status' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
            
            if not v in range(0,4):
                raise ValueError("Input data for 'job_status' must be an integer between 0 and 3. (provided value '%s')" % (value))
        
        self._shotgun_format_job_status(v) 


    def _input_format_total_render_time(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'total_render_time' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
            
        self._shotgun_format_total_render_time(v) 


    def _input_format_avg_frame_time(self, value):
        if value is not None:
            try:
                v = int(value)
            except ValueError:
                raise ValueError("Input data for 'avg_frame_time' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
            
        self._shotgun_format_avg_frame_time(v) 


    def _input_format_version_id(self, value):
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise ValueError("Input data for 'version_id' must be an integer. (provided value '%s' is a %s)" % (value, type(value)))
            
        self._shotgun_format_version_id(v) 


    def _shotgun_format_user(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'user') ] = {'type':'HumanUser', 'id': value}


    def _shotgun_format_project(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'project') ] = {'type':'Project', 'id': value}


    def _shotgun_format_task(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'task') ] = {'type':'Task', 'id': value}


    def _shotgun_format_shot(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'shot') ] = {'type':value[0], 'id': value[1]}


    def _shotgun_format_first_frame(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'first_frame') ] = value


    def _shotgun_format_last_frame(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'last_frame') ] = value


    def _shotgun_format_frame_count(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'frame_count') ] = value


    def _shotgun_format_job_status(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'job_status') ] = self.version_statuses[value]


    def _shotgun_format_total_render_time(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'total_render_time') ] = value


    def _shotgun_format_avg_frame_time(self, value):
        self.shotgun_input[ self._config.get('version_fields', 'avg_frame_time') ] = value


    def _shotgun_format_version_id(self, value):
        # id field is non-negotiable ;)
        self.shotgun_input['id'] = value

    
    def _shotgun_format_name(self, value):
        if self.version_name_replace_spaces:
            value = re.sub('\s+', self.version_name_space_token, value)
        if self.version_name_force_lowercase:
            value = value.lower()
        self.shotgun_input[ self._config.get('version_fields', 'name') ] = value


    def extract_version_data(self):
        """
        Translation method to convert Version data provided by render queue to the common Shotgun format.

        - extracts the values
        - validates they are okay
        - converts them into Shotgun-friendly format

        Any invalid data provided will raise a ValueError. Any data keys that are provided which are not
        enabled in the config will be silently ignored

        """
        for field, value in self.raw_input.iteritems():
            if field in ['name','user','project','task','shot','first_frame','last_frame','frame_count','job_status','total_render_time','avg_frame_time','version_id']:
                getattr(self, '_input_format_%s' % field)(value)
            # ignore everything else
            else:
                pass   

    

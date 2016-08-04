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

import sys
import logging
# shotgun_io modules
try:
    import io_entity_queries
except Exception, e:
    msg = "There is a problem in your entity_query_config module: %s" % e
    logging.error(msg)
    sys.exit(1)
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


class OutputDefault (object):
    def __init__(self): 
        self.value = None
        self.entity_list = io_entity_queries.entity_queries.keys()       

    
    def format_user(self, v):
        out = False
        if v:
            out = {
                'id': v.get('id'),
                'name': v.get('login'),
                'type': v.get('type')
                }
        return out
    
    def format_users(self, vals):
        out = []
        for u in vals:
            out.append(self.format_user(u))
        return out

    def format_task(self, v):
        out = None
        if v:
            project_id = None
            project_name = ''
            entity_id = None
            entity_type = None
            entity_name = ''

            project = v.get('project')
            if project:
                project_id = project.get('id')
                project_name = project.get('name')
            entity = v.get('entity')
            if entity:
                entity_id = entity.get('id')
                entity_type = entity.get('type')
                entity_name = entity.get('name')
            out = {
                'id':v.get('id'),
                'project_id':project_id, 
                'entity_type':entity_type, 
                'entity_id':entity_id, 
                'display_name': "%s | %s | %s" % (project_name, entity_name, v.get('content'))
                }
        return out
     
    def format_tasks(self, vals):
        out = []
        for t in vals:
          out.append(self.format_task(t))
        return out

    def format_project(self, v):
        out = None
        if v:
            out = {'id':v.get('id'), 'name':v.get('name')}
        return out

    def format_projects(self, vals):
        out = []
        for p in vals:
            out.append(self.format_project(p))
        return out

    def format_entity(self, v):
        out = None
        if v:
            nk = 'name'
            if not nk in v:
                nk = 'code'
            out = {'type':v.get('type'), 'id':v.get('id'), 'name':v.get(nk)}
        return out       

    def format_entities(self, vals):
        out = []
        for e in vals:
            out.append(self.format_entity(e))    
        return out

    def format_version_fields(self, vals):
        out = vals
        return out

    def format_version_statuses(self, vals):
        out = vals       
        return out

    def format_version_name_templates(self, vals):
        out = vals        
        return out

    def format_thumbnail_id(self, vals):
        out = vals        
        return out

    def format_movie_upload(self, vals):
        out = vals        
        return out

    def format_config(self, vals):
        out = vals        
        return out

    def format_version_create(self, vals):
        out = vals       
        return out

    def format_version_update(self, vals):
        out = vals        
        return out

    def format_version_delete(self, vals):
        out = vals        
        return out

    # call format_ method to format the results. If no method exists and
    # the list type is in the defined io_entity_queries dictionary, then
    # return the results as formatted entities. Otherwise return results
    # as is.
    def format_output(self, listtype, vals):
        try:
            out = getattr(self, 'format_%s' % listtype)(vals)
        except AttributeError:
            if listtype not in self.entity_list:
                return vals
            else:
                out = self.format_entities(vals)            
        return out


class OutputCmdLine (OutputDefault):
    def __init__(self): 
        super(OutputCmdLine, self).__init__()
        self.value = None        

    # used for validating user
    def format_user(self, vals):
        out = ""
        if vals:
            out = "%d %s\n" % (vals.get('id'), vals.get('login'))
        return out
    
    def format_users(self, vals):
        out = ""
        for u in vals:
            out += self.format_user(u)
        return out

    def format_task(self, val):
        out = ""
        p_id = p_name = ""
        e_id = e_name = e_type = ""
        # verify Task has a Project
        if isinstance(val['project'], dict):
            p_id = val['project']['id']
            p_name = val['project']['name']
        # verify Task has an entity
        if isinstance(val['entity'], dict):
            e_id = val['entity']['id']
            e_type = val['entity']['type']
            e_name = val['entity']['name']
        out += "%s,%s,%s,%s %s | %s | %s\n" % (val['id'], p_id, e_type, e_id, p_name, e_name, val['content'])       
        return out

    def format_tasks(self, vals):
        out = ""
        for t in vals:
            out += self.format_task(t)
        return out

    def format_project(self,v):
        out = "%d %s\n" % (v['id'], v['name'])        
        return out

    def format_projects(self, vals):
        out = ""
        for p in vals:
            out += self.format_project(p)      
        return out
    
    def format_entity(self, e):
        out = ""
        nk = 'name'
        if not nk in e:
            nk = 'code'
        out = "%s %d %s\n" % (e['type'], e['id'], e[nk]) 
        return out       

    def format_entities(self, vals):
        out = ""
        for e in vals:
            out += self.format_entity(e)      
        return out

    def format_env_variables(self, vals):
        """
        user 123 kp
        project 123 Demo Project
        name 010_0001 / anim / kp
        shot 123 010_0001
        task 123
        """
        out = ""
        for k,v in vals.iteritems():
            if k == 'user':
                out += "%s %s" % (k, self.format_users([v]))
            else:
                try:
                    out += "%s %s" % (k, getattr(self, 'format_%s' % k)(v))
                except AttributeError, e:
                    # don't need to raise an error we'll return stuff as-is
                    # raise AttributeError('No output method defined for format_%s()' % listtype)
                    out += "%s %s\n" % (k, v)
                    # print "Error formatting key '%s' in hash. No formatter defined" % (k)
        return out
            # try:
            #     if k == 'name':
            #         out += "name %s\n" % v
            #     elif k == 'task':
            #         out += "task %s" % self.format_task(v)
            #     elif k == 'user':
            #         out += "%s %d %s" % (k, v['id'], v['login'])
            #     else:
            #         out += "%s %d %s" % (k, v['id'], v['name'])
            # except:
            #     print "Error formatting key '%s' in hash\n%s" % (k,vals)
        # return out

    def format_version_fields(self, vals):
        out = ""
        for type, fields in vals.iteritems():
            out += "\n[%s]\n" % type
            for name in fields:
                out += "%s\n" % name
        return out[1:-1]

    def format_version_statuses(self, vals):
        out = ""
        for s in vals:
            out += "%s\n" % (s)            
        return out[:-1]

    def format_version_name_templates(self, vals):
        out = ""
        out = "\n".join( [t.strip() for t in vals] )
        # if we want to strip the ${} out of it, this is the quick and dirty method.
        # return "\n".join( [t.replace("${","").replace("}","").strip() for t in templates] )
        return out

    def format_config(self, vals):
        out = ""
        if vals:
            for section, items in vals.iteritems():
                out += "\n[%s]" % section
                for key, val in items.iteritems():
                    out += "\n%s: %s" % (key, val)
                out += "\n"
        return out[1:-1]

    def format_version_create(self, vals):
        out = vals['id']       
        return out

    def format_version_update(self, vals):
        out = vals['id']        
        return out

    def format_version_delete(self, vals):
        if vals is False:
            # only get False here if Version exists but is already deleted
            # otherwise shotgun_io would have already raised an exception
            logging.warning('Version appears to have already been deleted.')


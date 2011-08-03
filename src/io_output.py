#!/usr/bin/env python

import sys
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


class OutputDefault (object):
    def __init__(self): 
        self.value = None        

    
    def format_user(self, vals):
        out = False
        if vals:
            out = {
                'id': vals.get('id'),
                'name': vals.get('login')
                }

        return out
    
    def format_users(self, vals):
        out = []
        for u in vals:
            out.append({'id':u['id'], 'name':u['login']})
        return out

    def format_tasks(self, vals):
        out = []
        for t in vals:
            project_id = None
            project_name = ''
            entity_id = None
            entity_type = None
            entity_name = ''

            project = t.get('project')
            if project:
                project_id = project.get('id')
                project_name = project.get('name')
            entity = t.get('entity')
            if entity:
                entity_id = entity.get('id')
                entity_type = entity.get('type')
                entity_name = entity.get('name')
            
            out.append(
                {
                    'id':t['id'], 
                    'project_id': project_id, 
                    'entity_type': entity_type, 
                    'entity_id': entity_id, 
                    'display_name': "%s | %s | %s" % (project_name, entity_name, t['content'])
                })
        return out

    def format_projects(self, vals):
        out = []
        for p in vals:
            out.append({'id':p['id'], 'name':p['name']})
        return out

    def format_projectsandtasks(self, vals):
        out = vals
        return out

    def format_shots(self, vals):
        out = []
        for e in vals:
            out.append(
                {
                    'id': e.get('id'),
                    'name': e.get('code'),
                })
        return out

    def format_assets(self, vals):
        out = []
        for e in vals:
            out.append(
                {
                    'id': e.get('id'),
                    'name': e.get('code'),
                })
        return out

    def format_assetsandshots(self, vals):
        out = []
        for e in vals:
            out.append(
                {
                    'id': e.get('id'),
                    'name': e.get('code'),
                    'type': e.get('type'),
                })
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

    def format_version_create(self, vals):
        out = vals       
        return out

    def format_version_update(self, vals):
        out = vals        
        return out

    def format_output(self, listtype, vals):
        try:
            out = getattr(self, 'format_%s' % listtype)(vals)
        except AttributeError:
            # don't need to raise an error we'll return stuff as-is
            # raise AttributeError('No output method defined for format_%s()' % listtype)
            return vals
        return out


class OutputCmdLine (OutputDefault):
    def __init__(self): 
        super(OutputCmdLine, self).__init__()
        self.value = None        

    
    def format_user(self, vals):
        out = ""
        if vals:
            out += "%d" % (vals['id'])
        return out
    
    def format_users(self, vals):
        out = ""
        for u in vals:
            out += "%d %s\n" % (u['id'], u['login'])
        return out

    def format_tasks(self, vals):
        out = ""
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
            out += "%s,%s,%s,%s %s | %s | %s\n" % (t['id'], p_id, e_type, e_id, p_name, e_name, t['content'])       
        return out

    def format_projects(self, vals):
        out = ""
        for p in vals:
            out += "%d %s\n" % (p['id'], p['name'])        
        return out

    def format_shots(self, vals):
        out = ""
        for s in vals:
            out += "%d %s\n" % (s['id'], s['code'])        
        return out

    def format_assets(self, vals):
        out = self.format_shots(vals)        
        return out

    def format_assetsandshots(self, vals):
        out = self.format_shots(vals)           
        return out

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


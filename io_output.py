#!/usr/bin/env python

class OutputDefault (object):
    def __init__(self): 
        self.value = None        

    
    def format_user(self, vals):
        out = vals

        return out

    
    def format_users(self, vals):
        out = vals

        return out


    def format_tasks(self, vals):
        out = vals
        
        return out


    def format_projects(self, vals):
        out = vals
        
        return out


    def format_projectsandtasks(self, vals):
        out = vals
        
        return out


    def format_shots(self, vals):
        out = vals
        
        return out


    def format_assets(self, vals):
        out = vals
        
        return out


    def format_assetsandshots(self, vals):
        out = vals
        
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


    def format_scenepath_parse(self, vals):
        out = vals
        
        return out


    def format_output(self, listtype, vals):
        if listtype == 'user':
            out = self.format_user(vals)

        if listtype == 'users':
            out = self.format_users(vals)

        elif listtype == 'tasks':
            out = self.format_tasks(vals)

        elif listtype == 'projects':
            out = self.format_projects(vals)

        elif listtype == 'projectsandtasks':
            out = self.format_projectsandtasks(vals)

        elif listtype == 'shots':
            out = self.format_shots(vals)

        elif listtype == 'assets':
            out = self.format_assets(vals)

        elif listtype == 'assetsandshots':
            out = self.format_assetsandshots(vals)
       
        elif listtype == 'version_fields':
            out = self.format_version_fields(vals)
       
        elif listtype == 'version_statuses':
            out = self.format_version_statuses(vals)
       
        elif listtype == 'version_name_templates':
            out = self.format_version_name_templates(vals)
       
        elif listtype == 'thumbnail_id':
            out = self.format_thumbnail_id(vals)

        elif listtype == 'scenepath_parse':
            out = self.format_scenepath_parse(vals)

        return out





class OutputCmdLine (OutputDefault):
    def __init__(self): 
        super(OutputCmdLine, self).__init__()
        self.value = None        

    
    def format_user(self, vals):
        out = ""
        if vals:
            out += "%d\n" % (vals['id'])

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


    def format_projectsandtasks(self, vals):
        out = "output format for 'projectsandtasks' is not yet implemented"
        # for p in vals:
        #     out += "%d %s\n" % (p['id'], p['name'])
        
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
        out = vals

        return out


    def format_version_statuses(self, vals):
        out = ""
        for s in vals:
            out += "%s\n" % (s)            

        return out


    def format_version_name_templates(self, vals):
        out = ""
        out = "\n".join( [t.strip() for t in vals] )
        # if we want to strip the ${} out of it, this is the quick and dirty method.
        # return "\n".join( [t.replace("${","").replace("}","").strip() for t in templates] )

        return out


    def format_scenepath_parse(self, vals):
        out = ""
        if vals:
            out = "\n".join( [v.strip() for v in vals] )

        return out


    # def format_output(self, listtype, vals):
    #     if listtype == 'user':
    #         out = self.format_user(vals)

    #     if listtype == 'users':
    #         out = self.format_users(vals)

    #     elif listtype == 'tasks':
    #         out = self.format_tasks(vals)

    #     elif listtype == 'projects':
    #         out = self.format_projects(vals)

    #     elif listtype == 'projectsandtasks':
    #         out = self.format_projectsandtasks(vals)

    #     elif listtype == 'shots':
    #         out = self.format_shots(vals)

    #     elif listtype == 'assets':
    #         out = self.format_assets(vals)

    #     elif listtype == 'assetsandshots':
    #         out = self.format_assetsandshots(vals)
       
    #     elif listtype == 'version_fields':
    #         out = self.format_version_fields(vals)
       
    #     elif listtype == 'version_statuses':
    #         out = self.format_version_statuses(vals)
       
    #     elif listtype == 'version_name_templates':
    #         out = self.format_version_name_templates(vals)

    #     elif listtype == 'thumbnail_id':
    #         out = self.format_thumbnail_id(vals)

    #     return out





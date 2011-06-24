#!/usr/bin/env python

import shotgun_io
import pprint

if __name__ == "__main__":

    io = shotgun_io.ShotgunIO()
    
    # # list users
    # pprint.pprint(io.list_entities('users'))

    # # list projects
    # pprint.pprint(io.list_entities('projects'))

    # # list tasks for user
    # pprint.pprint(io.list_entities('tasks', user_id=55))

    # list shots
    # pprint.pprint(io.list_entities('shots', project_id=65))

    # list assets
    # pprint.pprint(io.list_entities('assets', project_id=65))

    # list assetsandshots
    # pprint.pprint(io.list_entities('assetsandshots', project_id=65))

    # list projectsandtasks
    # pprint.pprint(io.list_entities('projectsandtasks', user_id=55))

    # list fucknuts
    # pprint.pprint(io.list_entities('fucknuts'))

    # list version name templates
    # pprint.pprint(io.list_version_name_templates())

    # validate user
    # pprint.pprint(io.validate_user('kp'))

    # list version fields
    # pprint.pprint(io.list_version_fields())

    # list version status values
    # pprint.pprint(io.list_version_status_values())

    # parse scene path for project and shot
    result = io.parse_scene_path_for_project_and_shot("/Users/kp/some/ice_age/100_010/layout.ma")
    if result:
        print "project: %s, shot: %s" % (result[0], result[1])
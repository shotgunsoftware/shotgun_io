#!/usr/bin/env python

import sys
sys.path.append('./src')
import shotgun_io
import pprint

if __name__ == "__main__":

    io = shotgun_io.ShotgunIO()
    
    # get users
    # pprint.pprint(io.get_entities('users'))

    # get projects
    # pprint.pprint(io.get_projects())

    # # list tasks for user
    # pprint.pprint(io.get_entities('tasks', user_id=55))

    # list shots
    # pprint.pprint(io.get_entities('shots', project_id=65))

    # list assets
    # pprint.pprint(io.get_entities('assets', project_id=65))

    # list assetsandshots
    # pprint.pprint(io.get_entities('assetsandshots', project_id=65))

    # list projectsandtasks
    # pprint.pprint(io.get_entities('projectsandtasks', user_id=55))

    # list fucknuts
    # pprint.pprint(io.get_entities('fucknuts'))

    # list version name templates
    # print io.get_version_name_templates()

    # validate user
    # pprint.pprint(io.validate_user('kp'))

    # list version fields
    # pprint.pprint(io.get_version_fields())

    # list version status values
    # pprint.pprint(io.get_version_status_values())

    # parse scene path for project and shot
    # result = io.get_entities_from_file_path("/Users/kp/some/ice_age/100_010/layout.ma")
    # if result:
    #     print "project: %s, shot: %s" % (result[0], result[1])

    # getconfig
    # pprint.pprint(io.get_config())
    
    # getworkflow
    #print io.get_workflow()

    # create version
    # data = {
    #     # 'version_id': 123,
    #     'name':'Test Version',
    #     'project':65,
    #     'user':55,
    #     # 'task':557,
    #     'shot':{'type':'Shot','id':860},
    #     'first_frame':1,
    #     'last_frame':100,
    #     'frame_count':100,
    #     'job_status': 0,
    #     'total_render_time':500,
    #     'avg_frame_time':5,
    #     'thumbnail':'/Users/kp/foobar.jpg',
    #     'movie_path':'/Users/kp/Desktop/screenshots/100_120_v3.mov',
    #     'frames_path':'/Users/kp/Desktop/screenshots/100_120_v3.@@@@.exr',
    # }
    # result = io.create_version(data)
    # pprint.pprint(result)
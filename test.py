#!/usr/bin/env python

import sys
sys.path.append('./src')
import shotgun_io
import pprint

if __name__ == "__main__":

    io = shotgun_io.ShotgunIO()
    
    # get users
    # [{
    #     'id': 32, 
    #     'name': 'kp'
    # }]
    # pprint.pprint(io.get_entities('users'))

    # get projects
    # [{
    #     'id': 4, 
    #     'name': 'Demo Project'
    # }]
    # pprint.pprint(io.get_projects())

    # get tasks for user
    # [{
    #     'display_name': 'Demo Project | Shot 4 | Match Move',
    #     'entity_id': 5,
    #     'entity_type': 'Shot',
    #     'id': 34,
    #     'project_id': 4
    # }]
    # pprint.pprint(io.get_entities('tasks', user_id=32))

    # list shots
    # [{
    #     'id': 4, 
    #     'name': 'Shot 2'
    # }]
    # pprint.pprint(io.get_entities('shots', project_id=4))

    # list assets
    # [{
    #     'id': 4, 
    #     'name': 'Asset 3'
    # }]
    # pprint.pprint(io.get_entities('assets', project_id=4))

    # list assetsandshots
    # [
    #   {'id': 6, 'name': 'Shot 5', 'type': 'Shot'},
    #   {'id': 3, 'name': 'Asset 1', 'type': 'Asset'}
    # ]
    # pprint.pprint(io.get_entities('assetsandshots', project_id=4))

    # list fucknuts
    # shotgun_io.ShotgunIOError: entity_type value 'fucknuts' is invalid. Valid options are ['tasks', 'users', 'assetsandshots', 'shots', 'projects', 'assets']
    # pprint.pprint(io.get_entities('fucknuts'))

    # list version name templates
    # ['${project} / ${shot} / ${task} / ${user}', '${project}_${shot}_${task}_${user}', '${project} ${shot} ${task} ${jobid}', '${shot}_${task} ${jobid}']
    # print io.get_version_name_templates()

    # validate user
    # False | {'id': 32, 'name': 'stewie'}
    # pprint.pprint(io.validate_user('kp'))

    # list version fields
    # pprint.pprint(io.get_version_fields())

    # list version status values
    # {
    #     'checkbox': ['sg_frames_have_slate', 'sg_movie_has_slate'],
    #     'entity': ['entity', 'project', 'sg_task', 'task_template', 'user'],
    #     'float': ['sg_frames_aspect_ratio', 'sg_movie_aspect_ratio'],
    #     ...
    # }
    # pprint.pprint(io.get_version_status_values())

    # getconfig
    # {
    #     'advanced': {
    #         'custom_module': '',
    #         'input_format': 'default',
    #         'output_format': 'default',
    #         'workflow': 'task'
    #         },
    #     'shotgun': {
    #         'application_key': '6b9b9fd56e8b6ce34bdb35db52f18c983bc536c8',
    #         'script_name': 'rush',
    #         'url': 'https://rush.shotgunstudio.com'},
    #     ...
    # }
    # pprint.pprint(io.get_config())
    
    # getworkflow
    # task | project_shot
    # print io.get_workflow()

    # create version
    # {
    #     'code': 'Test Version_v005',
    #     'entity': {'id': 6, 'name': 'Shot 5', 'type': 'Shot'},
    #     'frame_count': 100,
    #     'frame_range': '1-100',
    #     'id': 153,
    #     'project': {'id': 4, 'name': 'Demo Project', 'type': 'Project'},
    #     'sg_avg_frame_time': 5,
    #     'sg_first_frame': 1,
    #     'sg_job_id': 'contrail.9999',
    #     'sg_last_frame': 100,
    #     'sg_path_to_frames': '/Users/kp/Documents/shotgun/maya/horse_gallop/frames/horseGallop_final.####.jpg',
    #     'sg_path_to_movie': '/Users/kp/Desktop/screenshots/100_120_v3.mov',
    #     'sg_status_list': 'qd',
    #     'sg_task': {'id': 14, 'name': 'Match Move', 'type': 'Task'},
    #     'sg_total_render_time': 500,
    #     'thumbnail_id': 20,
    #     'type': 'Version',
    #     'user': {'id': 32, 'name': 'kp', 'type': 'HumanUser'}
    # }
    # data = {
    #     # 'version_id': 123,
    #     'name':'Test Version',
    #     'description':'This is a test yo'
    #     'project':4,
    #     'user':32,
    #     'task':14,
    #     'shot':{'type':'Shot','id':6},
    #     'first_frame':1,
    #     'last_frame':100,
    #     'frame_count':100,
    #     'frame_range':'1-100',
    #     'job_status': 0,
    #     'total_render_time':500,
    #     'avg_frame_time':5,
    #     'thumbnail':'/Users/kp/foobar.jpg',
    #     'movie_path':'/Users/kp/Desktop/screenshots/100_120_v3.mov',
    #     'frames_path':'/Users/kp/Documents/shotgun/maya/horse_gallop/frames/horseGallop_final.####.jpg',
    #     'job_id': 'contrail.9999',
    # }
    # result = io.create_version(data)
    # pprint.pprint(result)

    # update version
    # {
    #     'code': 'Test Version_v005',
    #     'entity': {'id': 6, 'name': 'Shot 5', 'type': 'Shot'},
    #     'frame_count': 100,
    #     'frame_range': '1-100',
    #     'id': 153,
    #     'project': {'id': 4, 'name': 'Demo Project', 'type': 'Project'},
    #     'sg_avg_frame_time': 5,
    #     'sg_first_frame': 1,
    #     'sg_job_id': 'contrail.9999',
    #     'sg_last_frame': 100,
    #     'sg_path_to_frames': '/Users/kp/Documents/shotgun/maya/horse_gallop/frames/horseGallop_final.####.jpg',
    #     'sg_path_to_movie': '/Users/kp/Desktop/screenshots/100_120_v3.mov',
    #     'sg_status_list': 'qd',
    #     'sg_task': {'id': 14, 'name': 'Match Move', 'type': 'Task'},
    #     'sg_total_render_time': 500,
    #     'thumbnail_id': 20,
    #     'type': 'Version',
    #     'user': {'id': 32, 'name': 'kp', 'type': 'HumanUser'}
    # }
    # data = {
    #     'version_id': 153,
    #     'name':'Test Version_zzz',
    #     'project':4,
    #     'user':39,
    #     'task':14,
    #     'shot':{'type':'Asset','id':621},
    #     'first_frame':9,
    #     'last_frame':900,
    #     'frame_count':892,
    #     'frame_range':'9-900_zzz',
    #     'job_status': 1,
    #     'total_render_time':900,
    #     'avg_frame_time':9,
    #     'movie_path':'/Users/kp/Desktop/screenshots/100_120_v1.mov',
    #     'frames_path':'/Users/kp/Documents/shotgun/maya/horse_gallop/frames/horseGallop_final.#.jpg',
    #     'job_id': 'contrail.9999_zzz',
    # }
    # result = io.update_version(data)
    # pprint.pprint(result)
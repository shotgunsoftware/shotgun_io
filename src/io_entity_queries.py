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

"""
Defines the default entity types, filters, fields, and order for the list
methods for querying Shotgun for populating menus for artist submissions. The
keys define valid option values for the get_entities() method or the -l option
on the command line.
""" 
entity_queries = {
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
        'filters': [
            ['sg_status', 'is_not', 'Archive'],
            ['name', 'is_not', 'Template Project']],
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
    'elements': {
        'entity_type': 'Element',
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
            {'field_name':'project','direction':'asc'},
            {'field_name':'entity','direction':'asc'},
            {'field_name':'content','direction':'asc'}],
        'project_required': False,
        'user_required': True,
        },
}

"""Defines the list of entity types to use in the advanced workflow.
Each value in the list below must exist as a key in the entity_queries
dictionary above and define a valid query.
"""
advanced_workflow_entities = ['shots','assets','elements']

"""Defines the default query filter used by validate_user()
"""
validate_user = {
    'entity_type': 'HumanUser',
    'filters': [['sg_status_list', 'is', 'act']],
    'fields': ['id','login'],
}


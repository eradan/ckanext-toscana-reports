import re

from ast import literal_eval
from jinja2 import Markup

from ckan import model
from ckan.logic import get_action

from ckan.lib.helpers import organizations_available

import logging

log = logging.getLogger(__name__)

def go_up_tree(publisher):
    '''Provided with a publisher object, it walks up the hierarchy and yields
    each publisher, including the one you supply.
    Essentially this is a slower version of Group.get_parent_group_hierarchy
    because it returns Group objects, rather than dicts. And it includes the
    publisher you supply.
    '''
    yield publisher
    for parent in publisher.get_parent_groups(type='organization'):
        for grandparent in go_up_tree(parent):
            yield grandparent

def go_down_tree(publisher):
    '''Provided with a publisher object, it walks down the hierarchy and yields
    each publisher, including the one you supply.
   
    Essentially this is a slower version of Group.get_children_group_hierarchy
    because it returns Group objects, rather than dicts.
    '''
    yield publisher
    for child in publisher.get_children_groups(type='organization'):
        for grandchild in go_down_tree(child):
            yield grandchild

def get_schema_options():
    context = {'model': model, 'session': model.Session}
    return get_action('schema_list')(context, {})

def organization_list(top=False):
    if top:
        organizations = model.Group.get_top_level_groups(type='organization')
    else:
        organizations = model.Session.query(model.Group).\
            filter(model.Group.type=='organization').\
            filter(model.Group.state=='active').order_by('title')
    for organization in organizations:
        yield (organization.name, organization.title)

def group_get_users(group, capacity):
    return group.members_of_type(model.User, capacity=capacity)


link_regex = None

def linkify(string):
    global link_regex
    if link_regex is None:
        link_regex = re.compile(r'(^|\s|\()(https?://[^\s"]+?)([\.;]?($|\s|\)))')
    return Markup(link_regex.sub(r'\1<a href="\2" target="_blank">\2</a>\3', string))

def orgs_for_admin_report():
    context = {'model': model, 'session': model.Session}
    admin_orgs = organizations_available(permission='admin')
#    relationship_managers = literal_eval(config.get('dgu.relationship_managers', '{}'))
#    allowed_orgs = relationship_managers.get(c.user, [])
#    if allowed_orgs:
#        data_dict = {
#            'organizations': allowed_orgs,
#            'all_fields': True,
#        }
#        rm_orgs = get_action('organization_list')(context, data_dict)
#    else:
#        rm_orgs = []
    all_orgs = {}
#    for org in (admin_orgs + rm_orgs):
    for org in admin_orgs:
       all_orgs[org['name']] = org
    return sorted(all_orgs.values(), key=lambda x: x['title'])


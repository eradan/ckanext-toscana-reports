from helpers import go_up_tree, go_down_tree, get_schema_options, organization_list, group_get_users, linkify, orgs_for_admin_report

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckan.model as model
import ckan.lib.helpers as h

from ckan.common import _, g, c
from ckanext.report.interfaces import IReport


class DatiToscanaReportsPlugin(plugins.SingletonPlugin):
    '''Dati Toscana Reports plugin.
    '''
    plugins.implements(IReport)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    def get_helpers(self):
        '''Register the most_popular_groups() function above as a template
        helper function.

        '''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {
		'go_up_tree': go_up_tree,
		'go_down_tree': go_down_tree,
		'get_schema_options': get_schema_options,
		'organization_list': organization_list,
		'group_get_users': group_get_users,
		'linkify': linkify,
		'orgs_for_admin_report': orgs_for_admin_report
	}

    # IConfigurer

    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, 'templates')


    # IReport

    def register_reports(self):
        """Register details of an extension's reports"""
        import reports
        return [
#                reports.publisher_activity_report_info,
#                reports.publisher_resources_info,
#                reports.unpublished_report_info,
                reports.datasets_without_resources_info,
#                reports.admin_editor_info,
                reports.licence_report_info,
                reports.pdf_datasets_report_info,
                reports.html_datasets_report_info,
                ]



import collections
import datetime
import logging
import os

from paste.deploy.converters import asbool

from ckan import model
from ckan.common import OrderedDict

import ckan.plugins as p

from ckanext.report import lib
from helpers import go_up_tree, group_get_users, organization_list

log = logging.getLogger(__name__)

def get_quarter_dates(datetime_now):
    '''Returns the dates for this (current) quarter and last quarter. Uses
    calendar year, so 1 Jan to 31 Mar etc.'''
    now = datetime_now
    month_this_q_started = (now.month - 1) // 3 * 3 + 1
    this_q_started = datetime.datetime(now.year, month_this_q_started, 1)
    this_q_ended = datetime.datetime(now.year, now.month, now.day)
    last_q_started = datetime.datetime(
                      this_q_started.year + (this_q_started.month-3)/12,
                      (this_q_started.month-4) % 12 + 1,
                      1)
    last_q_ended = this_q_started - datetime.timedelta(days=1)
    return {'this': (this_q_started, this_q_ended),
            'last': (last_q_started, last_q_ended)}


def get_quarter_dates_merged(datetime_now):
    '''Returns the dates for the period including this (current) quarter and
    the last quarter. Uses calendar year, so 1 Jan to 31 Mar etc.'''
    now = datetime_now
    month_this_q_started = (now.month - 1) // 3 * 3 + 1
    this_q_started = datetime.datetime(now.year, month_this_q_started, 1)
    this_q_ended = datetime.datetime(now.year, now.month, now.day)
    last_q_started = datetime.datetime(
                      this_q_started.year + (this_q_started.month-3)/12,
                      (this_q_started.month-4) % 12 + 1,
                      1)
    last_q_ended = this_q_started - datetime.timedelta(days=1)
    return {'this_and_last': (last_q_started, this_q_ended)}


def _get_activity(organization_name, include_sub_organizations, periods):
    from paste.deploy.converters import asbool

    created = dict((period_name, []) for period_name in periods)
    modified = dict((period_name, []) for period_name in periods)

    # These are the authors whose revisions we ignore, as they are trivial
    # changes. NB we do want to know about revisions by:
    # * harvest (harvested metadata)
    # * dgu (NS Stat Hub imports)
    # * Fix national indicators
    system_authors = ('autotheme', 'co-prod3.dh.bytemark.co.uk',
                      'Date format tidier', 'current_revision_fixer',
                      'current_revision_fixer2', 'fix_contact_details.py',
                      'Repoint 410 Gone to webarchive url',
                      'Fix duplicate resources',
                      'fix_secondary_theme.py',
                      )
    system_author_template = 'script%'  # "%" is a wildcard

    if organization_name:
        organization = model.Group.by_name(organization_name)
        if not organization:
            raise p.toolkit.ObjectNotFound()

    if not organization_name:
        pkgs = model.Session.query(model.Package)\
                    .all()
    else:
        pkgs = model.Session.query(model.Package)
        pkgs = lib.filter_by_organizations(pkgs, organization,
                                           include_sub_organizations).all()

    for pkg in pkgs:
        created_ = model.Session.query(model.PackageRevision)\
            .filter(model.PackageRevision.id == pkg.id) \
            .order_by("revision_timestamp asc").first()

        pr_q = model.Session.query(model.PackageRevision, model.Revision)\
            .filter(model.PackageRevision.id == pkg.id)\
            .filter_by(state='active')\
            .join(model.Revision)\
            .filter(~model.Revision.author.in_(system_authors)) \
            .filter(~model.Revision.author.like(system_author_template))

#            .join(model.ResourceGroup)\
#            .join(model.ResourceRevision,
#                  model.ResourceGroup.id == model.ResourceRevision.resource_group_id)\

        rr_q = model.Session.query(model.Package, model.ResourceRevision, model.Revision)\
            .filter(model.Package.id == pkg.id)\
            .filter_by(state='active')\
            .join(model.Revision)\
            .filter(~model.Revision.author.in_(system_authors))\
            .filter(~model.Revision.author.like(system_author_template))
        pe_q = model.Session.query(model.Package, model.PackageExtraRevision, model.Revision)\
            .filter(model.Package.id == pkg.id)\
            .filter_by(state='active')\
            .join(model.PackageExtraRevision,
                  model.Package.id == model.PackageExtraRevision.package_id)\
            .join(model.Revision)\
            .filter(~model.Revision.author.in_(system_authors))\
            .filter(~model.Revision.author.like(system_author_template))

        for period_name in periods:
            period = periods[period_name]
            # created
            if period[0] < created_.revision_timestamp < period[1]:
                published = not asbool(pkg.extras.get('unpublished'))
                created[period_name].append(
                    (created_.name, created_.title, lib.dataset_notes(pkg),
                     'created', period_name,
                     created_.revision_timestamp.isoformat(),
                     created_.revision.author, published))

            # modified
            # exclude the creation revision
            period_start = max(period[0], created_.revision_timestamp)
            prs = pr_q.filter(model.PackageRevision.revision_timestamp > period_start)\
                        .filter(model.PackageRevision.revision_timestamp < period[1])
            rrs = rr_q.filter(model.ResourceRevision.revision_timestamp > period_start)\
                        .filter(model.ResourceRevision.revision_timestamp < period[1])
            pes = pe_q.filter(model.PackageExtraRevision.revision_timestamp > period_start)\
                        .filter(model.PackageExtraRevision.revision_timestamp < period[1])
            authors = ' '.join(set([r[1].author for r in prs] +
                                   [r[2].author for r in rrs] +
                                   [r[2].author for r in pes]))
            dates = set([r[1].timestamp.date() for r in prs] +
                        [r[2].timestamp.date() for r in rrs] +
                        [r[2].timestamp.date() for r in pes])
            dates_formatted = ' '.join([date.isoformat()
                                        for date in sorted(dates)])
            if authors:
                published = not asbool(pkg.extras.get('unpublished'))
                modified[period_name].append(
                    (pkg.name, pkg.title, lib.dataset_notes(pkg),
                        'modified', period_name,
                        dates_formatted, authors, published))
    return created, modified


def last_resource_deleted(pkg):

    #    .join(model.ResourceGroup) \
    resource_revisions = model.Session.query(model.ResourceRevision) \
        .join(model.Package) \
        .filter_by(id=pkg.id) \
        .order_by(model.ResourceRevision.revision_timestamp) \
        .all()
    previous_rr = None
    # go through the RRs in reverse chronological order and when an active
    # revision is found, return the rr in the previous loop.
    for rr in resource_revisions[::-1]:
        if rr.state == 'active':
            if not previous_rr:
                # this happens v.v. occasionally where a resource_revision and
                # its resource somehow manages to have a different
                # resource_group_id
                return None, ''
            return previous_rr.revision_timestamp, previous_rr.url
        previous_rr = rr
    return None, ''

def datasets_without_resources(organization, include_sub_organizations=False):
    pkg_dicts = []
    query = model.Session.query(model.Package)\
                .filter_by(state='active')\
                .order_by(model.Package.title)
    if organization:
        query = lib.filter_by_organizations(query, organization,
                                        include_sub_organizations)
    for pkg in query.all():
        if len(pkg.resources) != 0 or \
                pkg.extras.get('unpublished', '').lower() == 'true':
            continue
        deleted, url = last_resource_deleted(pkg)
        pkg_dict = OrderedDict((
            ('name', pkg.name),
            ('title', pkg.title),
            ('metadata created', pkg.metadata_created.isoformat()),
            ('metadata modified', pkg.metadata_modified.isoformat()),
            ('last resource deleted', deleted.isoformat() if deleted else None),
            ('last resource url', url),
            ('dataset_notes', lib.dataset_notes(pkg)),
            ))
        pkg_dicts.append(pkg_dict)
    return {'table': pkg_dicts}


def dataset_without_resources_report_option_combinations():
    for organization in lib.all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
            yield {'organization': organization,
                   'include_sub_organizations': include_sub_organizations}

datasets_without_resources_info = {
    'name': 'datasets-without-resources',
    'title': 'Dataset senza risorse',
    'description': 'Dataset a cui non sono assosicate risorse (data URL), esclusi i dataset non ancora pubblicati.',
    'option_defaults': None,
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False),
                                    )),
    'option_combinations': dataset_without_resources_report_option_combinations,
    'generate': datasets_without_resources,
    'template': 'report/datasets_without_resources.html',
    }


def user_is_admin(user, org=None):
    import ckan.lib.helpers as helpers
    if org:
        return helpers.check_access('organization_update', {'id': org.id})
    else:
        # Are they admin of any org?
        return len(user.get_groups('organization', capacity='admin')) > 0

def admin_editor_authorize(user, options):
    if not user:
        return False

    if user.sysadmin:
        return True

    if options.get('org', False):
        org_name = options["org"]
        org = model.Session.query(model.Group) \
                   .filter_by(name=org_name) \
                   .first()
        if not org:
            return False

        if user_is_admin(user, org):
            return True
        else:
            return False
    else:
        # Allow them to see front page / see report on report index
        if user_is_admin(user):
            return True

    return False

# Licence report

def licence_report(organization, include_sub_organizations=False):
    '''
    Returns a dictionary detailing licences for datasets in the
    organisation specified, and optionally sub organizations.
    '''
    # Get packages
    if organization:
        top_org = model.Group.by_name(organization)
        if not top_org:
            raise p.toolkit.ObjectNotFound('Publisher not found')

        if include_sub_organizations:
            orgs = lib.go_down_tree(top_org)
        else:
            orgs = [top_org]
        pkgs = set()
        for org in orgs:
            org_pkgs = model.Session.query(model.Package)\
                            .filter_by(state='active')
            org_pkgs = lib.filter_by_organizations(
                org_pkgs, organization,
                include_sub_organizations=False)\
                .all()
            pkgs |= set(org_pkgs)
    else:
        pkgs = model.Session.query(model.Package)\
                    .filter_by(state='active')\
                    .all()

    # Get their licences
    packages_by_licence = collections.defaultdict(list)
    rows = []
    num_pkgs = 0
    for pkg in pkgs:
        if asbool(pkg.extras.get('unpublished')) is True:
            # Ignore unpublished datasets
            continue
        licence_tuple = (pkg.license_id or '',
                         pkg.license.title if pkg.license else '',
                         pkg.extras.get('licence', ''))
        packages_by_licence[licence_tuple].append((pkg.name, pkg.title))
        num_pkgs += 1

    for licence_tuple, dataset_tuples in sorted(packages_by_licence.items(),
                                                key=lambda x: -len(x[1])):
        license_id, license_title, licence = licence_tuple
        dataset_tuples.sort(key=lambda x: x[0])
        dataset_names, dataset_titles = zip(*dataset_tuples)
        licence_dict = OrderedDict((
            ('license_id', license_id),
            ('license_title', license_title),
            ('licence', licence),
            ('dataset_titles', '|'.join(t for t in dataset_titles)),
            ('dataset_names', ' '.join(dataset_names)),
            ))
        rows.append(licence_dict)

    return {
        'num_datasets': num_pkgs,
        'num_licences': len(rows),
        'table': rows,
        }


def licence_combinations():
    for organization in lib.all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
                yield {'organization': organization,
                       'include_sub_organizations': include_sub_organizations}


licence_report_info = {
    'name': 'licence',
    'title': 'Licenze',
    'description': 'Licenze usate nei dataset.',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False))),
    'option_combinations': licence_combinations,
    'generate': licence_report,
    'template': 'report/licence_report.html',
    }


# Datasets only in PDF

def pdf_datasets_report(organization, include_sub_organizations=False):
    '''
    Returns datasets that have data in PDF format, by organization.
    '''
    # Get packages
    query = model.Session.query(model.Package)\
                .filter_by(state='active')
    if organization:
        query = lib.filter_by_organizations(query, organization,
                                        include_sub_organizations)
    pkgs = query.all();

    # See if PDF
    num_datasets_published = 0
    num_datasets_only_pdf = 0
    packages = []
    # use yield_per, otherwise memory use just goes up til the script is killed
    # by the os.
    for pkg in pkgs:
        if p.toolkit.asbool(pkg.extras.get('unpublished')):
            continue
        num_datasets_published += 1

        formats = set([res.format.lower() for res in pkg.resources
                       if res.resource_type != 'documentation'])
        if 'pdf' not in formats:
            continue

        data_formats = formats - set(('html', '', None))
        if data_formats == set(('pdf',)):
            num_datasets_only_pdf += 1
            packages.append(pkg)

    rows = []
    for pkg in packages:
        pkg_dict = OrderedDict((
            ('name', pkg.name),
            ('title', pkg.title),
            ('metadata created', pkg.metadata_created.isoformat()),
            ('metadata modified', pkg.metadata_modified.isoformat()),
            ('dataset_notes', lib.dataset_notes(pkg)),
            ))
        rows.append(pkg_dict)

    return {'table': rows,
            'num_datasets_published': num_datasets_published,
            'num_datasets_only_pdf': num_datasets_only_pdf,
            }


def pdf_datasets_combinations():
    for organization in lib.all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
                yield {'organization': organization,
                       'include_sub_organizations': include_sub_organizations}


pdf_datasets_report_info = {
    'name': 'pdf_datasets',
    'title': 'Dataset PDF',
    'description': 'Dataset con risorse esclusivamente in formato PDF.',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False))),
    'option_combinations': pdf_datasets_combinations,
    'generate': pdf_datasets_report,
    'template': 'report/pdf_datasets_report.html',
    }


# Datasets with HTML link

def html_datasets_report(organization, include_sub_organizations=False):
    '''
    Returns datasets that only have an HTML link, by organization.
    '''

    # Get packages
    query = model.Session.query(model.Package)\
                .filter_by(state='active')
    if organization:
        query = lib.filter_by_organizations(query, organization,
                                        include_sub_organizations)

    pkgs = query.all()
    # See if HTML
    num_datasets_published = 0
    num_datasets_only_html = 0
    datasets_only_html = []
    # use yield_per, otherwise memory use just goes up til the script is killed
    # by the os.
    for pkg in pkgs:
        if p.toolkit.asbool(pkg.extras.get('unpublished')):
            continue
        num_datasets_published += 1

        formats = set([res.format.lower() for res in pkg.resources
                       if res.resource_type != 'documentation'])
        if 'html' not in formats:
            continue
        #org = pkg.get_organization().name

        data_formats = formats - set(('asp', '', None))
        if data_formats == set(('html',)):
            num_datasets_only_html += 1
            datasets_only_html.append(pkg)

    rows = []
    for pkg in datasets_only_html:
        row = OrderedDict((
            ('name', pkg.name),
            ('title', pkg.title),
            ('metadata created', pkg.metadata_created.isoformat()),
            ('metadata modified', pkg.metadata_modified.isoformat()),
            ('dataset_notes', lib.dataset_notes(pkg)),
            ))
        rows.append(row)

    return {'table': rows,
            'num_datasets_published': num_datasets_published,
            'num_datasets_only_html': num_datasets_only_html,
            }


def html_datasets_combinations():
    for organization in lib.all_organizations(include_none=True):
        for include_sub_organizations in (False, True):
                yield {'organization': organization,
                       'include_sub_organizations': include_sub_organizations}

html_datasets_report_info = {
    'name': 'html_datasets',
    'title': 'Dataset HTML',
    'description': 'Dataset con risorse che linkano esclusivamente ad una pagina HTML.',
    'option_defaults': OrderedDict((('organization', None),
                                    ('include_sub_organizations', False))),
    'option_combinations': html_datasets_combinations,
    'generate': html_datasets_report,
    'template': 'report/html_datasets_report.html',
    }


def add_progress_bar(iterable, caption=None):
    try:
        # Add a progress bar, if it is installed
        import progressbar
        bar = progressbar.ProgressBar(widgets=[
            (caption + ' ') if caption else '',
            progressbar.Percentage(), ' ',
            progressbar.Bar(), ' ', progressbar.ETA()])
        return bar(iterable)
    except ImportError:
        return iterable



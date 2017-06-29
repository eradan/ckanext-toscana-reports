
# ckanext-toscana_reports
CKAN extension that provides customized reports for dati.toscana.it

## Contents

- [Overview](#overview)
- [License](#license)
- [Requirements](#requirements)
- [Installation](#installation)
- [Development Installation](#development-installation)
- [Contributing](#contributing)
- [Support, Communication and Credits](#support-communication-and-credits)


## License

**ckanext-toscana_reports** is Free and Open Source software and is licensed under the GNU Affero General Public License (AGPL) v3.0 whose full text may be found at:

http://www.fsf.org/licensing/licenses/agpl-3.0.html

## Overview 

This extension provides customized reports for for dati.toscana.it (integrated from ckanext-report).
Once installed access to http://dati.toscana.it/report to access reports.

## Requirements

The ckanext-toscana_reports extension has been developed for CKAN 2.5 or later.

It's based upon the ckanext-report infrustructure so it depends on previous installation and configutation of:
* [ckanext-report](https://github.com/datagovuk/ckanext-report): extension that provides a reporting infrastructure 
* [ckanext-qa](https://github.com/ckan/ckanext-qa): extension will check each of your dataset resources in CKAN and give them an 'openness score' based Tim Berners-Lee's five stars of opennes


## Installation

1. Go into your CKAN path for extension (like /usr/lib/ckan/default/src):
 
    `git clone https://github.com/eradan/ckanext-toscana-reports.git`

    `cd ckanext-toscana-theme`

    `pip install -e .`

2. Add ``datitoscana_reports`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at ``/etc/ckan/default/production.ini``).

3. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     `sudo service apache2 reload`

4. In order to keep reports up-to-date configure cron as follow:

    `30 0 * * * /usr/lib/ckan/default/bin/paster --plugin=ckanext-qa qa update --config=/etc/ckan/default/production.ini`

    `40 0 * * * /usr/lib/ckan/default/bin/paster --plugin=ckanext-report report generate --config=/etc/ckan/default/production.ini`

  
## Contributing

We welcome contributions in any form:

* pull requests for new features
* pull requests for bug fixes
* pull requests for documentation
* funding for any combination of the above

## Support, Communication and Credits

This work has been performed by [Hyperborea](http://www.hyperborea.com) with funding provided by Regione Toscana.

The work is provided as is and no warranty whatsoever is provided. 
Thanks to [DataGovUK](http://data.gov.uk) for the cooperation.
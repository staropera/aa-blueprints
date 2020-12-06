# AA Blueprints

This is an blueprints library app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA) that can be used to list blueprints for your corporation or alliance.

![License](https://img.shields.io/badge/license-GPL-green) ![python](https://img.shields.io/badge/python-3.6-informational) ![django](https://img.shields.io/badge/django-3.1-informational) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Features

- Lists blueprints owned by corporation or alliance (configurable with permissions)

# Installation

1. `pip install aa-blueprints`
1. Add 'blueprints' to `INSTALLED_APPS` in `settings/local.py`, run migrations, collectstatic, and restart your allianceserver.
1. Add the following automated task definition:

```python
CELERYBEAT_SCHEDULE['blueprints_update_all_blueprints'] = {
            'task': 'blueprints.tasks.update_all_blueprints',
            'schedule': crontab(minute=0, hour='*/1'),
}
```

# AA Blueprints

This is an blueprints library app for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA) that can be used to list blueprints for your corporation or alliance.

![release](https://img.shields.io/pypi/v/aa-blueprints?label=release) ![License](https://img.shields.io/badge/license-GPL-green) ![python](https://img.shields.io/badge/python-3.6-informational) ![django](https://img.shields.io/badge/django-3.1-informational) ![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white) ![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## Overview

## Features

- Lists blueprints owned by corporation or alliance (configurable with permissions)

# Installation

## Requirements

AA Blueprints needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse) to function. Please make sure it is installed before before continuing.

## Steps

### Step 1 - Install the Package

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

`pip install aa-blueprints`

### Step 2 - Configure AA

- Add 'blueprints' to `INSTALLED_APPS` in `settings/local.py`.
- Add the following automated task definition:

```python
CELERYBEAT_SCHEDULE['blueprints_update_all_blueprints'] = {
            'task': 'blueprints.tasks.update_all_blueprints',
            'schedule': crontab(minute=0, hour='*/1'),
}
```

### Step 3 - Finalize App installation

Run migrations & copy static files:

```bash
python manage.py migrate
python manage.py collectstatic
```

Restart your supervisor services for Auth

### Step 4 -

Load EVE Online type data from ESI:

```bash
python manage.py blueprints_load_types
```

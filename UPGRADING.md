# Upgrading
## 0.x.y -> 1.0.0

**WARNING: This is a DESTRUCTIVE operation. You will lose outstanding**
**requests as well as permissions to the blueprint app.**

### Step 1 - Preparation
Shut down your supervisor (any running server / worker processes).

### Step 2 - Clean the DB

Run the following SQL:
```sql
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS blueprints_blueprint;
DROP TABLE IF EXISTS blueprints_location;
DROP TABLE IF EXISTS blueprints_owner;
DROP TABLE IF EXISTS blueprints_request;
SET FOREIGN_KEY_CHECKS=1;
```

### Step 3 - Remove old permissions

Run the following in a django shell (`./manage.py shell`)
```python
from django.contrib.auth.models import Permission
Permission.objects.filter(content_type__app_label="blueprints").delete()
```

### Step 4 - Reset Migrations

Reset migrations for blueprints:
```
./manage.py migrate blueprints zero --fake
```

### Step 5 - Upgrade Package

```
pip install -U aa-blueprints
```

### Step 6 - Post-Install
```
./manage.py migrate
./manage.py collectstatic
```

### Step 7 - Completion
Bring your server back up, and enjoy the new version of blueprints!

# Translation Files

This directory contains translation files for the Launch Points Web application.

## Supported Languages

- English (en)
- German (de)

## Creating/Updating Translations

1. Extract translatable strings:
   ```
   python manage.py makemessages -l de
   python manage.py makemessages -l en
   ```

2. Edit the `.po` files in `de/LC_MESSAGES/` and `en/LC_MESSAGES/`

3. Compile translations:
   ```
   python manage.py compilemessages
   ```


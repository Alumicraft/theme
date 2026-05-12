# Backdesk App Notes

## Purpose

Backdesk is a Frappe/ERPNext app for shared Desk workspace fixes and styling. It is the renamed version of the former Monocore Theme app.

## Current App Identity

- Frappe app name: `backdesk`
- Install command: `bench --site YOUR_SITE install-app backdesk`
- GitHub repo: `https://github.com/Alumicraft/theme`
- Python package directory: `backdesk/`
- Asset base path: `/assets/backdesk/`

## Compatibility

The app is declared compatible with Frappe and ERPNext v15/v16:

- `frappe = ">=15.0.0,<17.0.0"`
- `erpnext = ">=15.0.0,<17.0.0"`

## Main Behavior

- `backdesk/public/css/workspace_fullwidth.css` keeps workspace pages full-width while avoiding broad resets inside workspace cards, widgets, and editor blocks.
- `backdesk/public/js/workspace_sidebar.js` ports the generic Frappe v16 sidebar fixes:
  - preserves filters when clicking filtered sidebar links
  - keeps duplicate DocType sidebar links highlighting correctly
  - prevents wrong workspace switching on List/Form routes
  - guards broken `TypeLink.get_path` failures
  - uses Backdesk-prefixed localStorage/debug names
- `backdesk/api.py` adds:
  - `boot_session` cleanup for broken sidebar items, spacers, section breaks, and desktop icon image fallbacks
  - `get_layout_with_icons` override for Desktop Layout icon images

## Deliberately Removed

- Old custom sidebar icon injection
- Phosphor icon CSS/CDN dependency
- Workspace Icon child DocType and empty settings UI
- Agent-only `CLAUDE.md`
- DCR-specific defaults, map behavior, HBR behavior, and Kanban styling

## Verification

Use these checks after edits:

```bash
python3 -m pytest -q
node --check backdesk/public/js/workspace_sidebar.js
PYTHONPYCACHEPREFIX=/private/tmp/codex_pycache python3 -m py_compile backdesk/hooks.py backdesk/api.py backdesk/install.py setup.py
git diff --check
```

## Deployment Note

Fresh installs should use `backdesk`. Sites that already had `monocore_theme` installed may need an uninstall/reinstall or migration plan because the Frappe app id changed.

# Monocore Theme - Claude Code Guide

## What this is

A Frappe/ERPNext custom app that provides workspace styling and Desk sidebar behavior fixes. Installed via `bench get-app` into a Frappe site.

## Project structure

```
monocore_theme/
  hooks.py              # App entry point: CSS/JS includes, install hooks
  api.py                # Boot/session helpers and whitelisted overrides
  install.py            # after_install / after_migrate: hides replaced workspaces
  public/
    css/workspace_fullwidth.css  # Workspace shell/background/navbar styling
    js/workspace_sidebar.js      # Workspace sidebar navigation and switching fixes
  monocore_theme/
    doctype/
      monocore_theme_settings/  # Single DocType reserved for app configuration
  patches/              # Data migration patches
```

## Key architectural decisions

### Workspace sidebar fixes are bundled separately
`workspace_sidebar.js` is focused on Frappe Desk workspace behavior: filtered sidebar links, duplicate DocType active states, workspace selection on List/Form routes, and route-scoped workspace full-width class toggling.

### Sidebar icons are native
The old custom sidebar-icon injection path has been removed. Frappe v16 native workspace/sidebar icon behavior is the source of truth.

## Common workflows

### Build assets after CSS/JS changes
```bash
bench build --app monocore_theme
```

### Full site rebuild
```bash
bench build && bench clear-cache
```

## API endpoints (all in api.py)

| Method | Purpose |
|--------|---------|
| `boot_session` | Normalizes workspace sidebar boot data and desktop icon image fallbacks |
| `get_layout_with_icons` | Merges Desktop Icon image fields into Desktop Layout JSON |

## Gotchas

- `hooks.py` `app_include_css` and `app_include_js` control what gets bundled. After editing, run `bench build`.
- `after_install` also runs `after_migrate` (both point to same function). It removes the app workspace and hides replaced standard workspaces.
- `HIDDEN_WORKSPACES` in `install.py` hides default Frappe workspaces that have custom replacements (e.g., "Buying" replaced by "Sales").

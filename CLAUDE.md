# Monocore Theme - Claude Code Guide

## What this is

A Frappe/ERPNext custom app that provides UI customizations: sidebar icons, shortcut groups, and theme styling. Installed via `bench get-app` into a Frappe site.

## Project structure

```
monocore_theme/
  hooks.py              # App entry point: CSS/JS includes, install hooks
  api.py                # Whitelisted API endpoints (frappe.call targets)
  install.py            # after_install / after_migrate: seeds settings, hides workspaces
  public/
    css/theme.css       # Sidebar icon styles (generic, works with JS injection)
    css/shortcut_group.css
    js/sidebar_icons.js # Fetches icon map from API, injects Phosphor icons into sidebar
    js/shortcut_group_renderer.js
    js/shortcut_group_block.js
  monocore_theme/
    doctype/
      monocore_theme_settings/  # Single DocType: app configuration
      workspace_icon/           # Child table row: workspace name + icon_class
      shortcut_group/           # DocType: groups of shortcut links
      shortcut_group_item/      # Child table row for shortcut group
  patches/              # Data migration patches
```

## Key architectural decisions

### Sidebar icons are JS-driven, not CSS-driven
`sidebar_icons.js` calls `monocore_theme.api.get_workspace_icons` to get a `{workspace: icon_class}` map from the database, then injects `<i class="ph-fill ph-{name}">` elements into the sidebar DOM. This makes icons configurable from Monocore Theme Settings without rebuilding assets.

### Phosphor Icons (Fill variant)
Icons use [Phosphor Icons](https://phosphoricons.com/) fill variant. The CDN CSS is loaded both via `hooks.py` (`app_include_css`) and via `@import` in `theme.css`. Icon classes follow the pattern `ph-{name}` (e.g., `ph-house`, `ph-gear`). The full mapping of defaults lives in `install.py:KNOWN_ICONS`.

### setInterval polling for sidebar DOM
The sidebar is rendered by Vue and Frappe re-renders it unpredictably. `sidebar_icons.js` uses `setInterval` (1s) to re-apply icons after re-renders. This is intentional - MutationObserver was tried and reverted (see git history).

## Common workflows

### Build assets after CSS/JS changes
```bash
bench build --app monocore_theme
```

### Full site rebuild
```bash
bench build && bench clear-cache
```

### Add a new default workspace icon
1. Add entry to `KNOWN_ICONS` dict in `install.py`
2. No CSS changes needed - the JS approach handles it automatically

### Change an icon at runtime
Go to Monocore Theme Settings > workspace_icons table, change the `icon_class` field, save, refresh the page.

## API endpoints (all in api.py)

| Method | Purpose |
|--------|---------|
| `get_workspace_icons` | Returns `{workspace: icon_class}` map |
| `sync_workspace_icons` | Syncs icons table with current public workspaces |
| `get_shortcut_groups(workspace)` | Returns shortcut groups for a workspace |
| `save_shortcut_group(data)` | Create/update a shortcut group |
| `delete_shortcut_group(name)` | Delete a shortcut group |

## Gotchas

- `hooks.py` `app_include_css` and `app_include_js` control what gets bundled. After editing, run `bench build`.
- The Phosphor CDN URL is pinned to `@2.1.1` in both `hooks.py` and `theme.css`.
- `after_install` also runs `after_migrate` (both point to same function). It seeds workspace_icons only if the table is empty.
- `HIDDEN_WORKSPACES` in `install.py` hides default Frappe workspaces that have custom replacements (e.g., "Buying" replaced by "Sales").

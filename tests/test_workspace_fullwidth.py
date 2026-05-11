from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


def test_workspace_fullwidth_css_scopes_to_workspace_shells():
    css = read("monocore_theme/public/css/workspace_fullwidth.css")

    assert 'body[data-route^="Workspaces/"]' in css
    assert "body:has(.workspace-body)" in css
    assert "--monocore-workspace-content-padding" in css
    assert ".layout-main-section-wrapper" in css
    assert ".container.page-body" in css
    assert "body.monocore-workspace-fullbleed .ce-block" not in css
    assert "body.monocore-workspace-fullbleed .widget" not in css
    assert "body.monocore-workspace-fullbleed .number-card" not in css


def test_workspace_fullwidth_css_styles_workspace_background_and_navbar_only():
    css = read("monocore_theme/public/css/workspace_fullwidth.css")

    assert "--monocore-workspace-bg" in css
    assert "--monocore-workspace-navbar-bg" in css
    assert "body.monocore-workspace-fullbleed .navbar" in css
    assert 'body[data-route^="Workspaces/"] .navbar' in css
    assert "body:has(.workspace-body) .navbar" in css
    assert 'html[data-theme="dark"] body.monocore-workspace-fullbleed' in css
    assert "body .navbar {" not in css
    assert "body .page-container {" not in css


def test_workspace_sidebar_js_toggles_workspace_fullbleed_class():
    js = read("monocore_theme/public/js/workspace_sidebar.js")

    assert "inject_workspace_fullbleed_styles" in js
    assert "set_workspace_fullbleed_class" in js
    assert "workspace_slug_from_route" in js
    assert "monocore-workspace-fullbleed" in js
    assert "frappe.router.on" in js
    assert "body.monocore-workspace-fullbleed .main-section" in js
    assert "--monocore-workspace-content-padding" in js


def test_workspace_sidebar_js_ports_generic_navigation_fixes():
    js = read("monocore_theme/public/js/workspace_sidebar.js")

    assert "route_options_from_item" in js
    assert "frappe.route_options = opts" in js
    assert "patch_workspace_switch" in js
    assert "set_workspace_sidebar" in js
    assert "pick_correct_workspace" in js
    assert "fix_active" in js
    assert "patch_typelink_get_path" in js
    assert "monocore_workspace_for_" in js
    assert "monocore_sidebar_fix_doctype_workspace" in js
    assert "window.__monocore_sidebar_debug" in js


def test_workspace_sidebar_js_stays_generic():
    js = read("monocore_theme/public/js/workspace_sidebar.js").lower()

    assert "dcr_" not in js
    assert "__dcr_sidebar_debug" not in js
    assert "homebuildrequest" not in js
    assert "deals" not in js


def test_hooks_include_versioned_workspace_assets():
    hooks = read("monocore_theme/hooks.py")
    compact_hooks = " ".join(hooks.split())

    assert "MONOCORE_ASSET_VERSION" in hooks
    assert "versioned_asset" in hooks
    assert 'versioned_asset("/assets/monocore_theme/css/workspace_fullwidth.css")' in hooks
    assert 'versioned_asset("/assets/monocore_theme/js/workspace_sidebar.js")' in hooks
    assert "boot_session = \"monocore_theme.api.boot_session\"" in hooks
    assert '"frappe.desk.doctype.desktop_layout.desktop_layout.get_layout":' in compact_hooks
    assert '"monocore_theme.api.get_layout_with_icons"' in compact_hooks


def test_sidebar_icon_assets_are_not_bundled():
    hooks = read("monocore_theme/hooks.py")

    assert "sidebar_icons.js" not in hooks
    assert "phosphor-icons" not in hooks
    assert "theme.css" not in hooks


def test_sidebar_icon_management_code_is_removed():
    api = read("monocore_theme/api.py")
    install = read("monocore_theme/install.py")
    settings = read(
        "monocore_theme/monocore_theme/doctype/monocore_theme_settings/"
        "monocore_theme_settings.json"
    )
    patches = read("monocore_theme/patches.txt")

    assert "get_workspace_icons" not in api
    assert "sync_workspace_icons" not in api
    assert "Workspace Icon" not in api
    assert "KNOWN_ICONS" not in install
    assert "workspace_icons" not in install
    assert "Phosphor" not in settings
    assert "Workspace Icon" not in settings
    assert "setup_workspace_icons" not in patches


def test_api_contains_boot_sidebar_cleanup_and_desktop_icon_override():
    api = read("monocore_theme/api.py")

    assert "def boot_session(bootinfo):" in api
    assert "workspace_sidebar_item" in api
    assert 'item.get("type") != "Link"' in api
    assert 'item.get("link_to")' in api
    assert 'item.get("link_type") == "URL"' in api
    assert 'item["standard"] = True' in api
    assert 'item["indent"] = 1' in api
    assert "desktop_icons" in api
    assert 'item["icon_url"] = url' in api
    assert "def get_layout_with_icons():" in api
    assert '"Desktop Layout"' in api
    assert '"Desktop Icon"' in api


def test_pyproject_allows_erpnext_v16():
    pyproject = read("pyproject.toml")

    assert 'frappe = ">=15.0.0,<17.0.0"' in pyproject
    assert 'erpnext = ">=15.0.0,<17.0.0"' in pyproject

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


def test_workspace_fullwidth_css_scopes_to_workspace_shells():
    css = read("backdesk/public/css/workspace_fullwidth.css")

    assert 'body[data-route^="Workspaces/"]' in css
    assert "body:has(.workspace-body)" in css
    assert "--backdesk-workspace-content-padding" in css
    assert ".layout-main-section-wrapper" in css
    assert ".container.page-body" in css
    assert "body.backdesk-workspace-fullbleed .ce-block" not in css
    assert "body.backdesk-workspace-fullbleed .widget" not in css
    assert "body.backdesk-workspace-fullbleed .number-card" not in css


def test_workspace_fullwidth_css_styles_workspace_background_and_navbar_only():
    css = read("backdesk/public/css/workspace_fullwidth.css")

    assert "--backdesk-workspace-bg" in css
    assert "--backdesk-workspace-navbar-bg" in css
    assert "body.backdesk-workspace-fullbleed .navbar" in css
    assert 'body[data-route^="Workspaces/"] .navbar' in css
    assert "body:has(.workspace-body) .navbar" in css
    assert 'html[data-theme="dark"] body.backdesk-workspace-fullbleed' in css
    assert "body .navbar {" not in css
    assert "body .page-container {" not in css


def test_workspace_sidebar_js_toggles_workspace_fullbleed_class():
    js = read("backdesk/public/js/workspace_sidebar.js")

    assert "inject_workspace_fullbleed_styles" in js
    assert "set_workspace_fullbleed_class" in js
    assert "workspace_slug_from_route" in js
    assert "backdesk-workspace-fullbleed" in js
    assert "frappe.router.on" in js
    assert "body.backdesk-workspace-fullbleed .main-section" in js
    assert "--backdesk-workspace-content-padding" in js


def test_workspace_sidebar_js_ports_generic_navigation_fixes():
    js = read("backdesk/public/js/workspace_sidebar.js")

    assert "route_options_from_item" in js
    assert "frappe.route_options = opts" in js
    assert "patch_workspace_switch" in js
    assert "set_workspace_sidebar" in js
    assert "pick_correct_workspace" in js
    assert "fix_active" in js
    assert "patch_typelink_get_path" in js
    assert "backdesk_workspace_for_" in js
    assert "backdesk_sidebar_fix_doctype_workspace" in js
    assert "window.__backdesk_sidebar_debug" in js


def test_workspace_sidebar_js_stays_generic():
    js = read("backdesk/public/js/workspace_sidebar.js").lower()

    assert "dcr_" not in js
    assert "__dcr_sidebar_debug" not in js
    assert "homebuildrequest" not in js
    assert "deals" not in js


def test_hooks_include_versioned_workspace_assets():
    hooks = read("backdesk/hooks.py")
    compact_hooks = " ".join(hooks.split())

    assert "BACKDESK_ASSET_VERSION" in hooks
    assert "versioned_asset" in hooks
    assert 'versioned_asset("/assets/backdesk/css/workspace_fullwidth.css")' in hooks
    assert 'versioned_asset("/assets/backdesk/js/workspace_sidebar.js")' in hooks
    assert "boot_session = \"backdesk.api.boot_session\"" in hooks
    assert '"frappe.desk.doctype.desktop_layout.desktop_layout.get_layout":' in compact_hooks
    assert '"backdesk.api.get_layout_with_icons"' in compact_hooks


def test_sidebar_icon_assets_are_not_bundled():
    hooks = read("backdesk/hooks.py")

    assert "sidebar_icons.js" not in hooks
    assert "phosphor-icons" not in hooks
    assert "theme.css" not in hooks


def test_sidebar_icon_management_code_is_removed():
    api = read("backdesk/api.py")
    install = read("backdesk/install.py")
    patches = read("backdesk/patches.txt")
    settings_path = (
        ROOT
        / "backdesk/backdesk/doctype/backdesk_settings/"
        "backdesk_settings.json"
    )

    assert "get_workspace_icons" not in api
    assert "sync_workspace_icons" not in api
    assert "Workspace Icon" not in api
    assert "KNOWN_ICONS" not in install
    assert "workspace_icons" not in install
    assert "setup_workspace_icons" not in patches
    assert not settings_path.exists()


def test_api_contains_boot_sidebar_cleanup_and_desktop_icon_override():
    api = read("backdesk/api.py")

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


def test_visible_app_identity_is_backdesk():
    hooks = read("backdesk/hooks.py")
    setup = read("setup.py")
    pyproject = read("pyproject.toml")
    modules = read("backdesk/modules.txt")
    desktop = read("backdesk/config/desktop.py")
    install = read("backdesk/install.py")
    patch = read("backdesk/patches/v0_0_1/remove_module_workspace.py")
    readme = read("README.md")

    assert 'app_name = "backdesk"' in hooks
    assert 'app_title = "Backdesk"' in hooks
    assert 'app_publisher = "Backdesk"' in hooks
    assert 'app-name = "backdesk"' in pyproject
    assert 'name="backdesk"' in setup
    assert "Backdesk" in setup
    assert modules.strip() == "Backdesk"
    assert '"Backdesk"' in desktop
    assert '"Backdesk"' in install
    assert '"Backdesk"' in patch
    assert readme.startswith("# Backdesk")

    visible_text = "\n".join([hooks, setup, modules, desktop, install, patch, readme])
    assert "Monocore Theme" not in visible_text

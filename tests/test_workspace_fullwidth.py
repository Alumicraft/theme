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
    assert "body.backdesk-workspace-fullbleed .page-head" in css
    assert 'body[data-route^="Workspaces/"] .page-head' in css
    assert "body:has(.workspace-body) .page-head" in css
    assert "body.backdesk-workspace-fullbleed .layout-main-section" in css
    assert 'body[data-route^="Workspaces/"] .layout-main-section' in css
    assert "body.backdesk-workspace-fullbleed .navbar" in css
    assert 'body[data-route^="Workspaces/"] .navbar' in css
    assert "body:has(.workspace-body) .navbar" in css
    assert "body.backdesk-workspace-fullbleed [data-page-route=\"Workspaces\"] .widget.spacer" in css
    assert 'body[data-route^="Workspaces/"] [data-page-route="Workspaces"] .widget.spacer' in css
    assert 'html[data-theme="dark"] body.backdesk-workspace-fullbleed' in css
    assert "--backdesk-workspace-bg: var(--surface-menu-bar" in css
    assert "--backdesk-workspace-navbar-bg: var(--surface-menu-bar" in css
    assert "--backdesk-workspace-border: var(--sidebar-border-color" in css
    assert "#111418" not in css
    assert "#171b20" not in css
    assert "body .navbar {" not in css
    assert "body .page-container {" not in css
    assert "body.backdesk-workspace-fullbleed .widget {" not in css


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
    assert "patch_workspace_save_page" in js
    assert "backdesk.api.save_workspace_page" in js
    assert "response && response.exc" in js
    assert "current_content === content" in js
    assert '__("No changes made")' in js
    assert "request.then(handle_success)" in js
    assert "finish(true)" in js
    assert "workspace.reload()" in js
    assert "set_workspace_sidebar" in js
    assert "pick_correct_workspace" in js
    assert "fix_active" in js
    assert "patch_typelink_get_path" in js
    assert "backdesk_workspace_for_" in js
    assert "backdesk_sidebar_fix_doctype_workspace" in js
    assert "window.__backdesk_sidebar_debug" in js


def test_workspace_sidebar_js_routes_internal_filtered_url_links_in_current_tab():
    js = read("backdesk/public/js/workspace_sidebar.js")
    hooks = read("backdesk/hooks.py")

    assert "internal_list_route_from_anchor" in js
    assert "doctype_from_route_segment" in js
    assert "route_options_from_url(item.url, item)" in js
    assert "route_option_key(key, item)" in js
    assert "if (Object.keys(url_opts).length) return url_opts" in js
    assert "Object.assign({}, item" in js
    assert "link_to: parsed.doctype" in js
    assert 'item.link_type === "URL"' in js
    assert 'frappe.set_route(["List", parsed.doctype, parsed.view])' in js
    assert "window.__backdesk_sidebar_debug.lastUrlClick" in js
    assert 'BACKDESK_ASSET_VERSION = "20260601-7"' in hooks
    assert "sanitize_list_route_options" in js
    assert 'delete sanitized["Payment Request.status"]' in js


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
    assert '"frappe.desk.doctype.workspace.workspace.save_page":' in compact_hooks
    assert '"backdesk.api.save_workspace_page"' in compact_hooks


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


def test_install_makes_payment_request_status_filterable():
    install = read("backdesk/install.py")

    assert "make_payment_request_status_filterable()" in install
    assert '"Payment Request-status-in_standard_filter"' in install
    assert '"doc_type": "Payment Request"' in install
    assert '"field_name": "status"' in install
    assert '"property": "in_standard_filter"' in install
    assert '"property_type": "Check"' in install
    assert '"value": "1"' in install
    assert 'frappe.clear_cache(doctype="Payment Request")' in install


def test_payment_request_list_excludes_paid_by_default():
    hooks = read("backdesk/hooks.py")
    list_js = read("backdesk/public/js/payment_request_list.js")

    assert '"Payment Request": "public/js/payment_request_list.js"' in hooks
    assert 'frappe.listview_settings["Payment Request"]' in list_js
    assert 'filters: [["status", "!=", "Paid"]]' in list_js


def test_payment_request_query_condition_excludes_paid():
    hooks = read("backdesk/hooks.py")
    api = read("backdesk/api.py")

    assert '"Payment Request": "backdesk.api.payment_request_query_conditions"' in hooks
    assert "def payment_request_query_conditions(user=None):" in api
    assert "`tabPayment Request`.`status`" in api
    assert "!= 'Paid'" in api


def test_payment_request_reportview_override_excludes_paid():
    hooks = read("backdesk/hooks.py")
    api = read("backdesk/api.py")

    assert '"frappe.desk.reportview.get": "backdesk.api.reportview_get"' in hooks
    assert '"frappe.desk.reportview.get_count": "backdesk.api.reportview_get_count"' in hooks
    assert '"frappe.desk.reportview.get_list": "backdesk.api.reportview_get_list"' in hooks
    assert "def _append_payment_request_not_paid_filter():" in api
    assert 'form_dict.get("doctype") != "Payment Request"' in api
    assert '["Payment Request", "status", "!=", "Paid"]' in api
    assert "def reportview_get():" in api
    assert "def reportview_get_count():" in api
    assert "def reportview_get_list():" in api
    assert "return reportview.get()" in api
    assert "return reportview.get_count()" in api
    assert "return reportview.get_list()" in api


def test_payment_request_reportview_calls_exclude_paid_client_side():
    js = read("backdesk/public/js/workspace_sidebar.js")

    assert 'window.__backdesk_sidebar_debug.version = "20260601-7"' in js
    assert "patch_payment_request_reportview_call" in js
    assert "patch_payment_request_reportview_transport" in js
    assert "force_payment_request_not_paid" in js
    assert "force_payment_request_not_paid_body" in js
    assert '"frappe.desk.reportview.get": true' in js
    assert '"frappe.desk.reportview.get_count": true' in js
    assert '"frappe.desk.reportview.get_list": true' in js
    assert 'args.doctype !== "Payment Request"' in js
    assert '["Payment Request", "status", "!=", "Paid"]' in js
    assert "args.filters = JSON.stringify(filters)" in js
    assert "window.XMLHttpRequest.prototype.send" in js
    assert "window.fetch" in js
    assert "frappe\\.desk\\.reportview\\.(?:get|get_count|get_list)" in js


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


def test_api_contains_workspace_save_override():
    api = read("backdesk/api.py")

    assert "def save_workspace_page(" in api
    assert "def _can_edit_workspace(doc):" in api
    assert "is_workspace_manager()" in api
    assert "doc.content = blocks" in api
    assert "save_new_widget(doc, name, blocks, new_widgets or {})" in api
    assert "frappe.PermissionError" in api


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

from pathlib import Path
import importlib
import sys
import types


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


def load_api_with_frappe_stub():
    frappe = types.ModuleType("frappe")
    frappe._ = lambda value: value
    frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    frappe.parse_json = lambda value: value
    frappe.bold = lambda value: value
    frappe.throw = lambda *args, **kwargs: None
    frappe.PermissionError = Exception
    frappe.DoesNotExistError = Exception
    frappe.session = types.SimpleNamespace(user="Administrator")

    desk = types.ModuleType("frappe.desk")
    desktop = types.ModuleType("frappe.desk.desktop")
    desktop.save_new_widget = lambda *args, **kwargs: None
    doctype = types.ModuleType("frappe.desk.doctype")
    workspace_pkg = types.ModuleType("frappe.desk.doctype.workspace")
    workspace = types.ModuleType("frappe.desk.doctype.workspace.workspace")
    workspace.is_workspace_manager = lambda: True

    sys.modules["frappe"] = frappe
    sys.modules["frappe.desk"] = desk
    sys.modules["frappe.desk.desktop"] = desktop
    sys.modules["frappe.desk.doctype"] = doctype
    sys.modules["frappe.desk.doctype.workspace"] = workspace_pkg
    sys.modules["frappe.desk.doctype.workspace.workspace"] = workspace

    sys.modules.pop("backdesk.api", None)
    return importlib.import_module("backdesk.api")


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


def test_workspace_chart_values_remain_legible_in_dark_mode():
    css = read("backdesk/public/css/workspace_fullwidth.css")

    assert 'html[data-theme="dark"]' in css
    assert ".chart-container .data-point-value" in css
    assert "fill: var(--text-color, #f4f5f6) !important" in css
    assert 'body[data-route^="Workspaces/"] [data-page-route="Workspaces"] .widget.spacer' in css
    assert 'html[data-theme="dark"] body.backdesk-workspace-fullbleed' in css
    assert "--backdesk-workspace-navbar-foreground: #ffffff" in css
    assert "--icon-stroke: var(--backdesk-workspace-navbar-foreground)" in css
    assert ".navbar .nav-link" in css
    assert ".navbar .btn-reset" in css
    assert ".body-sidebar-container .standard-sidebar-item" in css
    assert ".body-sidebar-container .sidebar-item-label" in css
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
    assert "route_for_rule" in js
    assert "frappe.set_route(route_for_rule(item.link_to, label, opts, view))" in js
    assert "frappe.set_route(route_for_rule(parsed.doctype, label, opts, view))" in js
    assert "window.__backdesk_sidebar_debug.lastUrlClick" in js
    assert 'BACKDESK_ASSET_VERSION = "20260813-2"' in hooks
    assert "sanitize_list_route_options" in js
    assert "normalize_sidebar_anchor_hrefs" in js
    assert "clean_sidebar_href_for_item" in js
    assert "LIST_ROUTE_FILTER_RULES" in js
    assert 'id: "project-builds-active"' in js
    assert 'id: "service-parts-active"' in js
    assert 'id: "timesheets-draft"' in js
    assert 'id: "timesheets-submitted"' in js
    assert 'id: "sales-orders-active"' in js
    assert 'id: "sales-invoices-outstanding"' in js
    assert 'id: "purchase-orders-active"' in js
    assert 'id: "purchase-invoices-outstanding"' in js
    assert 'id: "suppliers-enabled"' in js
    assert 'id: "roles-all"' in js
    assert 'id: "payment-requests-unpaid"' in js
    assert 'clean_path: "/desk/project/view/kanban/Builds"' in js
    assert 'clean_path: "/desk/project/view/kanban/Service%2FParts"' in js
    assert 'clean_path: "/desk/payment-request/view/list"' in js
    assert 'project_type: "Build"' in js
    assert 'status: \'["not in",["Completed","Cancelled","Canceled"]]\'' in js
    assert 'project_type: \'["!=","Build"]\'' in js
    assert 'label: "Service/Parts"' in js
    assert "list_filter_rule_for_context" in js
    assert "clean_url_for_rule" in js
    assert "rule_matches_context" in js
    assert "if (rule.label && context.label === rule.label) return true;" in js
    assert "preferred_view_for_rule" in js
    assert "preferred_view_for_rule(item.link_to, label, opts)" in js
    assert "preferred_view_for_rule(parsed.doctype, label, opts)" in js
    assert 'preferred_view: "Kanban"' in js
    assert 'preferred_view_name: "Builds"' in js
    assert 'preferred_view_name: "Service/Parts"' in js
    assert "apply_default_filters_for_rule" in js
    assert "default_filters" in js
    assert "force_filters" not in js
    assert "delete sanitized[rule.strip_route_keys[i]]" in js
    assert '"docstatus"' in js
    assert '"Payment Request.docstatus"' in js
    assert '"stripe_payment_status"' in js
    assert '"Payment Request.stripe_payment_status"' in js
    assert '"Payment Request.status"' in js
    assert 'sanitized["Project.status"]' not in js


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


def test_payment_request_list_filter_is_not_registered_as_doctype_js():
    hooks = read("backdesk/hooks.py")
    list_js = read("backdesk/public/js/payment_request_list.js")

    assert "doctype_list_js" not in hooks
    assert '"Payment Request": "public/js/payment_request_list.js"' not in hooks
    assert 'frappe.listview_settings["Payment Request"]' in list_js
    assert 'filters: [["status", "not in", ["Paid", "Cancelled"]]]' in list_js


def test_payment_request_query_condition_is_not_hard_enforced():
    hooks = read("backdesk/hooks.py")
    api = read("backdesk/api.py")

    assert "permission_query_conditions" not in hooks
    assert "payment_request_query_conditions" not in api
    assert "`tabPayment Request`.`status`" not in api


def test_payment_request_reportview_override_is_not_hard_enforced():
    hooks = read("backdesk/hooks.py")
    api = read("backdesk/api.py")

    compact_hooks = " ".join(hooks.split())
    assert '"frappe.desk.reportview.get": "backdesk.api.reportview_get"' not in compact_hooks
    assert '"frappe.desk.reportview.get_count": "backdesk.api.reportview_get_count"' not in compact_hooks
    assert '"frappe.desk.reportview.get_list": "backdesk.api.reportview_get_list"' not in compact_hooks
    assert "_append_payment_request_active_filter" not in api
    assert "def reportview_get():" not in api
    assert "def reportview_get_count():" not in api
    assert "def reportview_get_list():" not in api


def test_workspace_sidebar_applies_removable_default_filters_client_side():
    js = read("backdesk/public/js/workspace_sidebar.js")

    assert 'window.__backdesk_sidebar_debug.version = "20260813-2"' in js
    assert "default_filters" in js
    assert "apply_default_filters_for_rule" in js
    assert "route_options_with_default_filters" in js
    assert "patch_payment_request_reportview_call" not in js
    assert "patch_payment_request_reportview_transport" not in js
    assert "apply_list_filter_rules_to_args" not in js
    assert "apply_list_filter_rules_to_params" not in js
    assert "apply_list_filter_rules_to_body" not in js
    assert "force_payment_request_not_paid" not in js
    assert "force_project_build_active" not in js
    assert '["Payment Request", "status", "not in", ["Paid", "Cancelled"]]' in js
    assert '["Project", "status", "not in", ["Completed", "Cancelled", "Canceled"]]' in js
    assert '["Project", "project_type", "!=", "Build"]' in js
    assert "defaults[route_option.key] = route_option.entry" in js
    assert "frappe.route_options = opts" in js


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


def test_boot_sidebar_cleanup_normalizes_spacers_in_list_and_object_payloads():
    api = load_api_with_frappe_stub()
    bootinfo = {
        "workspace_sidebar_item": {
            "jobs": {
                "items": [
                    {"type": "Section Break", "label": "Finance"},
                    {
                        "type": "Spacer",
                        "child": 1,
                        "nested_items": [
                            {"type": "Spacer"},
                        ],
                    },
                    {"type": "Link", "label": "Broken"},
                    {"type": "Link", "label": "External", "link_type": "URL"},
                ]
            },
            "recently-edited": [
                {"type": "Spacer"},
                {"type": "Section Break", "label": "Reports"},
            ],
        }
    }

    api.boot_session(bootinfo)

    jobs_items = bootinfo["workspace_sidebar_item"]["jobs"]["items"]
    edited_items = bootinfo["workspace_sidebar_item"]["recently-edited"]

    assert jobs_items[0]["indent"] == 1
    assert jobs_items[1]["standard"] is True
    assert jobs_items[1]["nested_items"][0]["standard"] is True
    assert jobs_items[2]["label"] == "External"
    assert edited_items[0]["standard"] is True
    assert edited_items[1]["indent"] == 1


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


def test_workspace_sidebar_patch_repairs_production_navigation_idempotently():
    patches = read("backdesk/patches.txt")
    patch = read("backdesk/patches/v0_0_2/repair_workspace_sidebar.py")

    assert "backdesk.patches.v0_0_2.repair_workspace_sidebar" in patches
    assert 'item.label == "Recievables"' in patch
    assert 'item.link_to = "Sales Order"' in patch
    assert 'item.link_to = "Payment Request"' in patch
    assert 'item.link_to = "User Permission"' in patch
    assert 'frappe.db.exists("Page", "permission-inspector")' in patch
    assert "doc.remove(item)" in patch
    assert 'existing_labels = {item.label for item in doc.items if item.label}' in patch
    assert 'if values["label"] in existing_labels:' in patch
    assert '"Sales Workflow"' in patch
    assert '"Quotations"' in patch
    assert '"Sales Orders"' in patch
    assert '"Sales Invoices"' in patch
    assert '"Active Builds"' in patch
    assert '"Active Service / Parts"' in patch
    assert '"Receivables Due"' in patch
    assert '"Payables Due"' in patch
    assert '"Profit and Loss New"' in patch
    assert '"type": "number_card"' in patch
    assert '"type": "chart"' in patch
    assert 'doc.content == "[]"' in patch
    assert '"Build Count": [' in patch
    assert '"Service/Parts Count": [' in patch
    assert '["Project", "status", "not in", ["Completed", "Cancelled", "Canceled"]]' in patch


def test_followup_patch_repairs_blank_overview_and_employee_names():
    patch = (
        ROOT
        / "backdesk"
        / "patches"
        / "v0_0_2"
        / "repair_overview_and_time_reporting.py"
    ).read_text()

    assert "required_ids.issubset(ids)" in patch
    assert "doc.content = json.dumps(OVERVIEW_CONTENT" in patch
    assert "NULLIF(e.last_name, '')" in patch
    assert "NULLIF(e.first_name, '')" in patch
    assert '"e.name, e.last_name, e.first_name"' in patch


def test_financial_chart_patch_uses_current_pnl_and_recognized_project_margin():
    patches = read("backdesk/patches.txt")
    workspace_patch = read("backdesk/patches/v0_0_2/repair_workspace_sidebar.py")
    chart_patch = read("backdesk/patches/v0_0_2/repair_financial_charts.py")
    followup_patch = read("backdesk/patches/v0_0_2/repair_financial_charts_v3.py")

    assert "backdesk.patches.v0_0_2.repair_financial_charts" in patches
    assert "backdesk.patches.v0_0_2.repair_financial_charts_v2" in patches
    assert "backdesk.patches.v0_0_2.repair_financial_charts_v3" in patches
    assert '"chart_name": "Profit and Loss New"' in workspace_patch
    assert 'filters={"chart_name": old_name}' in chart_patch
    assert 'data.get("chart_name") == old_name' in chart_patch
    assert '"from_fiscal_year": fiscal_year' in chart_patch
    assert '"to_fiscal_year": fiscal_year' in chart_patch
    assert 'account.root_type = \'Income\'' in chart_patch
    assert 'account.root_type = \'Expense\'' in chart_patch
    assert "gle.is_cancelled = 0" in chart_patch
    assert "p.total_consumed_material_cost" in chart_patch
    assert "GREATEST(" in chart_patch
    assert "p.name NOT IN ('INVENTORY', 'SHOP')" in chart_patch
    assert 'AS "Recognized Gross Margin:Currency:150"' in chart_patch
    assert 'doc.x_field = "project"' in chart_patch
    assert '"pink": "#F683AE"' in chart_patch
    assert '"blue": "#318AD8"' in chart_patch
    assert '"green": "#48BB74"' in chart_patch
    assert '("income", FRAPPE_CHART_COLORS["pink"])' in chart_patch
    assert '("expense", FRAPPE_CHART_COLORS["blue"])' in chart_patch
    assert '("profit", FRAPPE_CHART_COLORS["green"])' in chart_patch
    assert '[("recognized_gross_margin", FRAPPE_CHART_COLORS["pink"])]' in chart_patch
    assert "doc.show_values_over_chart = 1" in chart_patch
    assert 'doc.currency = "USD"' in chart_patch
    assert 'card_name = "Customer Deposits"' in chart_patch
    assert '"id": "backdesk-finance-customer-deposits"' in chart_patch
    assert "repair_worst_projects_chart()" in followup_patch
    assert "repair_finance_customer_deposits_card()" in followup_patch


def test_item_catalog_conversion_is_inventory_guarded():
    patch = read("backdesk/patches/v0_0_2/convert_items_to_non_stock_catalog.py")

    assert '"Stock Ledger Entry"' in patch
    assert '"Bin"' in patch
    assert '"BOM"' in patch
    assert '"Work Order"' in patch
    assert '"Stock Entry"' in patch
    assert "if populated:" in patch
    assert "SET is_stock_item = 0" in patch
    assert "include_item_in_manufacturing = 0" in patch
    assert 'NON_CATALOG_LINKS = {"BOMs", "Purchase Receipts"}' in patch


def test_product_workflow_correction_removes_inventory_links():
    patches = read("backdesk/patches.txt")
    patch = read("backdesk/patches/v0_0_2/correct_product_sales_workflow.py")

    assert "backdesk.patches.v0_0_2.correct_product_sales_workflow" in patches
    assert '"Inventory Workflow"' in patch
    assert '"Warehouses"' in patch
    assert '"Stock Entries"' in patch
    assert '"Quotations"' not in patch
    assert "for values in PRODUCT_LINKS:" in patch

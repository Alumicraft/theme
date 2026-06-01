import frappe
from frappe import _
from frappe.desk.desktop import save_new_widget
from frappe.desk.doctype.workspace.workspace import is_workspace_manager


def _boot_value(bootinfo, key, default=None):
    if isinstance(bootinfo, dict):
        return bootinfo.get(key, default)
    return getattr(bootinfo, key, default)


def _keep_sidebar_item(item):
    return (
        item.get("type") != "Link"
        or item.get("link_to")
        or item.get("link_type") == "URL"
    )


def _normalize_sidebar_items(items):
    cleaned = []
    for item in items or []:
        if not item or not _keep_sidebar_item(item):
            continue

        if item.get("type") == "Spacer":
            item["standard"] = True
        if item.get("type") == "Section Break" and not item.get("indent"):
            item["indent"] = 1
        if item.get("nested_items"):
            item["nested_items"] = _normalize_sidebar_items(item.get("nested_items"))
        cleaned.append(item)
    return cleaned


def boot_session(bootinfo):
    """Defensively normalize v15/v16 Desk workspace sidebar and icon data."""
    for item in (_boot_value(bootinfo, "desktop_icons", []) or []):
        url = item.get("logo_url") or item.get("icon_image")
        if url and not item.get("icon_url"):
            item["icon_url"] = url
        if item.get("icon_url") and item.get("icon"):
            item["icon"] = None

    sidebar_items = _boot_value(bootinfo, "workspace_sidebar_item", {}) or {}
    for _name, sidebar in sidebar_items.items():
        sidebar["items"] = _normalize_sidebar_items(sidebar.get("items") or [])


def _can_edit_workspace(doc):
    if doc.public:
        return is_workspace_manager()
    if doc.for_user == frappe.session.user:
        return True
    return is_workspace_manager()


@frappe.whitelist()
def save_workspace_page(name, public=0, new_widgets=None, blocks=None):
    """Save workspace editor blocks with Frappe v16 public workspace permissions."""
    public = frappe.parse_json(public)
    doc = frappe.get_doc("Workspace", name)

    if not _can_edit_workspace(doc):
        frappe.throw(
            _("Not permitted to edit Workspace {0}").format(frappe.bold(name)),
            frappe.PermissionError,
        )

    if not doc.type:
        doc.type = "Workspace"

    doc.content = blocks
    save_new_widget(doc, name, blocks, new_widgets or {})

    return {"name": name, "public": public, "label": doc.label}


@frappe.whitelist()
def get_layout_with_icons():
    """Merge Desktop Icon image fields into saved Desktop Layout JSON."""
    import json

    layout = None
    try:
        doc = frappe.get_doc("Desktop Layout", frappe.session.user)
        if doc.layout:
            layout = json.loads(doc.layout)
    except frappe.DoesNotExistError:
        frappe.clear_last_message()
        return None

    if not layout:
        return layout

    icons_with_images = frappe.get_all(
        "Desktop Icon",
        filters={"icon_image": ["is", "set"]},
        fields=["label", "logo_url", "icon_image"],
    )
    image_map = {i.label: i for i in icons_with_images}

    for item in layout:
        label = item.get("label")
        if label and label in image_map:
            img = image_map[label]
            if not item.get("logo_url"):
                item["logo_url"] = img.logo_url or img.icon_image
            if not item.get("icon_image"):
                item["icon_image"] = img.icon_image

    return layout


def _payment_request_filter_exists(filters):
    if isinstance(filters, dict):
        return any((key or "").split(".")[-1].strip("`") == "status" for key in filters)
    if not isinstance(filters, list):
        return False

    for condition in filters:
        if not isinstance(condition, (list, tuple)):
            continue
        if len(condition) >= 4 and condition[0] == "Payment Request" and condition[1] == "status":
            return True
        if len(condition) == 3 and condition[0] == "status":
            return True
    return False


def _normalize_reportview_filters(filters):
    if isinstance(filters, list):
        return filters
    if not isinstance(filters, dict):
        return []

    normalized = []
    for fieldname, value in filters.items():
        if (
            isinstance(value, (list, tuple))
            and value
            and str(value[0]).lower()
            in ("=", ">", "<", ">=", "<=", "!=", "like", "not like", "in", "not in", "between", "is")
        ):
            normalized.append([fieldname, value[0], value[1] if len(value) > 1 else None])
        else:
            normalized.append([fieldname, "=", value])
    return normalized


def _append_payment_request_not_paid_filter():
    """Force Payment Request list/reportview queries to exclude paid rows."""
    import json

    form_dict = frappe.local.form_dict
    if form_dict.get("doctype") != "Payment Request":
        return

    filters = form_dict.get("filters")
    if isinstance(filters, str) and filters:
        filters = json.loads(filters)
    elif not filters:
        filters = []

    filters = _normalize_reportview_filters(filters)

    if not _payment_request_filter_exists(filters):
        filters.append(["Payment Request", "status", "!=", "Paid"])

    form_dict["filters"] = json.dumps(filters)


@frappe.whitelist()
@frappe.read_only()
def reportview_get():
    from frappe.desk import reportview

    _append_payment_request_not_paid_filter()
    return reportview.get()


@frappe.whitelist()
@frappe.read_only()
def reportview_get_list():
    from frappe.desk import reportview

    _append_payment_request_not_paid_filter()
    return reportview.get_list()


@frappe.whitelist()
@frappe.read_only()
def reportview_get_count():
    from frappe.desk import reportview

    _append_payment_request_not_paid_filter()
    return reportview.get_count()


def payment_request_query_conditions(user=None):
    """Exclude paid Payment Requests from list/query views."""
    return "coalesce(`tabPayment Request`.`status`, '') != 'Paid'"

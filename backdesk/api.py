import frappe


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

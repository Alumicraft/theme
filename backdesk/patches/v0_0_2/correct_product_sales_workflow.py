import frappe

from backdesk.patches.v0_0_2.repair_workspace_sidebar import PRODUCT_LINKS, get_sidebar


OBSOLETE_INVENTORY_LABELS = {
    "Inventory Workflow",
    "Warehouses",
    "Stock Balance",
    "Stock Entries",
    "Material Requests",
    "Purchase Orders",
}


def execute():
    doc = get_sidebar("Products")
    if not doc:
        return

    changed = False
    for item in tuple(doc.items):
        if item.label in OBSOLETE_INVENTORY_LABELS:
            doc.remove(item)
            changed = True

    existing_labels = {item.label for item in doc.items if item.label}
    for values in PRODUCT_LINKS:
        if values["label"] in existing_labels:
            continue
        doc.append("items", values)
        existing_labels.add(values["label"])
        changed = True

    if changed:
        doc.save(ignore_permissions=True)

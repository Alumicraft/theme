import frappe


INVENTORY_GUARDS = (
    "Stock Ledger Entry",
    "Bin",
    "BOM",
    "Work Order",
    "Stock Entry",
)

NON_CATALOG_LINKS = {"BOMs", "Purchase Receipts"}


def execute():
    convert_items_if_inventory_is_unused()
    simplify_product_navigation()


def convert_items_if_inventory_is_unused():
    populated = [doctype for doctype in INVENTORY_GUARDS if frappe.db.count(doctype)]
    if populated:
        frappe.log_error(
            title="Backdesk item catalog conversion skipped",
            message="Inventory records exist in: " + ", ".join(populated),
        )
        return

    frappe.db.sql(
        """
        UPDATE `tabItem`
        SET is_stock_item = 0,
            include_item_in_manufacturing = 0
        WHERE IFNULL(is_stock_item, 0) != 0
           OR IFNULL(include_item_in_manufacturing, 0) != 0
        """
    )


def simplify_product_navigation():
    if not frappe.db.exists("Workspace Sidebar", "Products"):
        return

    doc = frappe.get_doc("Workspace Sidebar", "Products")
    removed = False
    for item in list(doc.items):
        if item.label in NON_CATALOG_LINKS:
            doc.remove(item)
            removed = True

    if removed:
        doc.save(ignore_permissions=True)

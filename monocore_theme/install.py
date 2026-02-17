import frappe


DEFAULT_ICONS = [
    {"workspace": "Home", "icon_class": "ph-house"},
    {"workspace": "Projects", "icon_class": "ph-folder-simple"},
    {"workspace": "Sales", "icon_class": "ph-arrow-up-right"},
    {"workspace": "Purchases", "icon_class": "ph-shopping-cart"},
    {"workspace": "Items", "icon_class": "ph-package"},
    {"workspace": "Manufacturing", "icon_class": "ph-factory"},
    {"workspace": "Customers", "icon_class": "ph-users"},
    {"workspace": "Accounting", "icon_class": "ph-coins"},
    {"workspace": "Users", "icon_class": "ph-user-plus"},
    {"workspace": "Terminal", "icon_class": "ph-terminal-window"},
]


def after_install():
    """Seed Monocore Theme Settings with default workspace icons."""
    settings = frappe.get_single("Monocore Theme Settings")

    if not settings.workspace_icons:
        for icon in DEFAULT_ICONS:
            settings.append("workspace_icons", icon)
        settings.save()
        frappe.db.commit()

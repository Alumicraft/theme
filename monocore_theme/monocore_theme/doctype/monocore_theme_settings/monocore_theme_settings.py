import frappe
from frappe.model.document import Document


class MonocoreThemeSettings(Document):
    def validate(self):
        """Sync table with actual workspaces when the doc is saved."""
        self.sync_workspace_icons()

    def sync_workspace_icons(self):
        """Add rows for any new workspaces, remove rows for deleted ones."""
        site_workspaces = set(
            frappe.get_all("Workspace", filters={"public": 1}, pluck="name")
        )

        # Build map of existing icon assignments
        existing = {}
        for row in self.workspace_icons:
            existing[row.workspace] = row.icon_class

        # Rebuild table: keep assigned icons, add missing workspaces
        self.workspace_icons = []
        for ws in sorted(site_workspaces):
            self.append("workspace_icons", {
                "workspace": ws,
                "icon_class": existing.get(ws, ""),
            })

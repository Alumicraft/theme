// Monocore Theme - Dynamic Sidebar Icons
// Fetches icon classes from Monocore Theme Settings and injects Phosphor icons
// into the sidebar, replacing default SVG icons.

(function () {
    let iconMap = null;

    function fetchIcons() {
        frappe.call({
            method: "monocore_theme.api.get_workspace_icons",
            async: true,
            callback: function (r) {
                if (r && r.message) {
                    iconMap = r.message;
                    applySidebarIcons();
                }
            },
        });
    }

    function applySidebarIcons() {
        if (!iconMap) return;

        document.querySelectorAll(".sidebar-item-container[item-name]").forEach(function (container) {
            let workspace = container.getAttribute("item-name");
            let iconClass = iconMap[workspace];
            if (!iconClass) return;

            let iconContainer = container.querySelector(".sidebar-item-icon");
            if (!iconContainer) return;

            // Skip if already processed with the correct icon
            let existing = iconContainer.querySelector("i.ph-fill");
            if (existing && existing.classList.contains(iconClass)) return;

            // Remove stale injected icon if icon class changed
            if (existing) {
                existing.remove();
            }

            // Hide the default SVG
            let svg = iconContainer.querySelector("svg");
            if (svg) {
                svg.style.display = "none";
            }

            // Inject Phosphor icon element
            let icon = document.createElement("i");
            icon.className = "ph-fill " + iconClass;
            iconContainer.appendChild(icon);
        });
    }

    // Fetch icons on page load, then poll for DOM re-renders
    frappe.ready(function () {
        fetchIcons();
        setInterval(applySidebarIcons, 1000);
    });
})();

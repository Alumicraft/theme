// Monocore Theme - Sidebar Icon Customization
// Uses Phosphor Icons to replace default ERPNext sidebar icons
// Icon map is loaded from Monocore Theme Settings

(function() {
    // Fallback defaults used until settings are fetched
    var iconMap = {
        "Home": "ph-house",
        "Projects": "ph-folder-simple",
        "Sales": "ph-arrow-up-right",
        "Purchases": "ph-shopping-cart",
        "Items": "ph-package",
        "Manufacturing": "ph-factory",
        "Customers": "ph-users",
        "Accounting": "ph-coins",
        "Users": "ph-user-plus",
        "Terminal": "ph-terminal-window",
    };

    var settingsLoaded = false;
    var swapping = false;

    function loadIconMap() {
        if (settingsLoaded) return;
        settingsLoaded = true;

        frappe.xcall("monocore_theme.api.get_workspace_icons")
            .then(function(map) {
                if (map && Object.keys(map).length) {
                    iconMap = map;
                }
                swapIcons();
            })
            .catch(function() {
                swapIcons();
            });
    }

    function swapIcons() {
        if (swapping) return;
        swapping = true;

        document.querySelectorAll(".sidebar-item-container.is-draggable").forEach(function(item) {
            var name = item.getAttribute("item-name");
            if (!iconMap[name]) return;

            var iconSpan = item.querySelector("span.sidebar-item-icon");
            if (!iconSpan) return;

            // Check if already swapped with the correct icon
            var existing = iconSpan.querySelector("i.ph-fill");
            if (existing) return;

            var svg = iconSpan.querySelector("svg");
            if (svg) svg.style.display = "none";

            var ph = document.createElement("i");
            ph.className = "ph-fill " + iconMap[name];
            ph.style.cssText = "font-size: 16px; line-height: 1; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px;";
            iconSpan.appendChild(ph);
        });

        swapping = false;
    }

    // Load settings then swap on initial load
    setTimeout(loadIconMap, 500);

    // Poll to keep icons applied when Frappe re-renders the sidebar
    setInterval(swapIcons, 500);

    // Also hook into Frappe's route change for faster response
    $(document).on("page-change", function() {
        setTimeout(swapIcons, 300);
    });
})();

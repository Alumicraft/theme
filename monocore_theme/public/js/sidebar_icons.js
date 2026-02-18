// Monocore Theme - Sidebar Icon Customization
// Uses Phosphor Icons to replace default ERPNext sidebar icons
// Icon map is loaded from Monocore Theme Settings

(function() {
    // Load Phosphor Fill CSS directly (bypasses Frappe asset pipeline caching)
    if (!document.querySelector('link[href*="phosphor-icons"][href*="fill"]')) {
        var link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css";
        document.head.appendChild(link);
    }

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
                // Settings not available yet — use defaults
                swapIcons();
            });
    }

    function swapIcons() {
        document.querySelectorAll(".sidebar-item-container.is-draggable").forEach(function(item) {
            var name = item.getAttribute("item-name");
            if (!iconMap[name]) return;

            var iconSpan = item.querySelector("span.sidebar-item-icon");
            if (!iconSpan || iconSpan.dataset.swapped) return;

            var svg = iconSpan.querySelector("svg");
            if (svg) svg.style.display = "none";

            var ph = document.createElement("i");
            ph.className = "ph-fill " + iconMap[name];
            ph.style.cssText = "font-size: 16px; line-height: 1; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px;";
            iconSpan.appendChild(ph);
            iconSpan.dataset.swapped = "true";
        });
    }

    // Load settings then swap on initial load
    setTimeout(loadIconMap, 500);
    setTimeout(swapIcons, 1500);
    setTimeout(swapIcons, 3000);

    // Watch for SPA page changes
    var observer = new MutationObserver(function(mutations) {
        var shouldSwap = mutations.some(function(m) {
            return m.addedNodes.length > 0;
        });
        if (shouldSwap) {
            setTimeout(swapIcons, 200);
        }
    });

    document.addEventListener("DOMContentLoaded", function() {
        var sidebar = document.querySelector(".desk-sidebar");
        if (sidebar) {
            observer.observe(sidebar, { childList: true, subtree: true });
        } else {
            var bodyObserver = new MutationObserver(function() {
                var sb = document.querySelector(".desk-sidebar");
                if (sb) {
                    observer.observe(sb, { childList: true, subtree: true });
                    bodyObserver.disconnect();
                    swapIcons();
                }
            });
            bodyObserver.observe(document.body, { childList: true, subtree: true });
        }
    });

    // Hook into Frappe's route change
    $(document).on("page-change", function() {
        setTimeout(swapIcons, 300);
        setTimeout(swapIcons, 800);
    });
})();

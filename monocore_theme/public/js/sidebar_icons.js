// Monocore Theme - Dynamic Sidebar Icons
// Fetches icon classes from Monocore Theme Settings and injects Phosphor icons
// into the sidebar, replacing default SVG icons.

(function () {
    let iconMap = null;

    function workspaceSlugFromRoute(route) {
        if (!route || !route.length) return null;

        let first = (route[0] || "").toLowerCase();
        if (route.length >= 2 && first === "workspaces" && route[1]) {
            if ((route[1] || "").toLowerCase() === "private" && route[2]) {
                return route[2].toLowerCase();
            }
            return route[1].toLowerCase();
        }

        return null;
    }

    function injectWorkspaceFullbleedStyles() {
        if (document.getElementById("monocore-workspace-fullbleed-js")) return;

        let style = document.createElement("style");
        style.id = "monocore-workspace-fullbleed-js";
        style.textContent = [
            "body.monocore-workspace-fullbleed { --page-max-width: none; --content-width: 100%; --monocore-workspace-content-padding: clamp(16px, 1.5vw, 24px); }",
            "body.monocore-workspace-fullbleed .main-section,",
            "body.monocore-workspace-fullbleed .page-container,",
            "body.monocore-workspace-fullbleed .page-wrapper,",
            "body.monocore-workspace-fullbleed .page-content,",
            "body.monocore-workspace-fullbleed .page-body,",
            "body.monocore-workspace-fullbleed .container.page-body,",
            "body.monocore-workspace-fullbleed .layout-main,",
            "body.monocore-workspace-fullbleed .layout-main-section-wrapper,",
            "body.monocore-workspace-fullbleed .layout-main-section,",
            "body.monocore-workspace-fullbleed .layout-main-section > .container,",
            "body.monocore-workspace-fullbleed .layout-main-section > .container-fluid {",
            "  max-width: none !important;",
            "  width: 100% !important;",
            "}",
            "body.monocore-workspace-fullbleed .page-body,",
            "body.monocore-workspace-fullbleed .container.page-body {",
            "  box-sizing: border-box !important;",
            "  padding-left: var(--monocore-workspace-content-padding, 20px) !important;",
            "  padding-right: var(--monocore-workspace-content-padding, 20px) !important;",
            "}",
            "body.monocore-workspace-fullbleed[data-route=\"Workspaces/Map\"] .page-body,",
            "body.monocore-workspace-fullbleed[data-route=\"Workspaces/Map\"] .container.page-body {",
            "  padding-left: 0 !important;",
            "  padding-right: 0 !important;",
            "}",
            "body.monocore-workspace-fullbleed[data-route=\"Workspaces/Map\"] .widget.custom-block-widget-box { padding: 0 !important; }",
        ].join("\n");
        document.head.appendChild(style);
    }

    function setWorkspaceFullbleedClass(reason) {
        try {
            let route = frappe.get_route ? frappe.get_route() : [];
            let isWorkspace = !!workspaceSlugFromRoute(route);

            if (!isWorkspace) {
                isWorkspace = !!document.querySelector(".workspace-body");
            }

            document.body.classList.toggle("monocore-workspace-fullbleed", isWorkspace);
            if (isWorkspace) {
                document.body.setAttribute("data-monocore-workspace-fullbleed", reason || "1");
            } else {
                document.body.removeAttribute("data-monocore-workspace-fullbleed");
            }
        } catch (e) {
            console.log("[Monocore Theme] workspace fullbleed class error:", e);
        }
    }

    function initWorkspaceFullbleed() {
        injectWorkspaceFullbleedStyles();
        setWorkspaceFullbleedClass("init");

        [200, 600, 1500, 3000].forEach(function (ms) {
            setTimeout(function () {
                setWorkspaceFullbleedClass("init+" + ms);
            }, ms);
        });

        let onRoute = function () {
            setWorkspaceFullbleedClass("route");
            setTimeout(function () {
                setWorkspaceFullbleedClass("route-300");
            }, 300);
        };

        if (frappe.router && typeof frappe.router.on === "function") {
            frappe.router.on("change", onRoute);
        } else {
            $(document).on("page-change", onRoute);
        }
    }

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

    // Fetch icons on first desk page-change, re-apply on every navigation
    $(document).on("page-change", function () {
        if (!iconMap) {
            fetchIcons();
        }
        applySidebarIcons();
    });

    // Poll for Vue re-renders between navigations
    setInterval(applySidebarIcons, 1000);

    $(document).ready(initWorkspaceFullbleed);
})();

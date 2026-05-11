app_name = "monocore_theme"
app_title = "Monocore Theme"
app_publisher = "Monocore"
app_description = "Custom UI theme and customizations for ERPNext"
app_email = "hello@monocore.com"
app_license = "MIT"

MONOCORE_ASSET_VERSION = "20260511-3"


def versioned_asset(path):
    return f"{path}?v={MONOCORE_ASSET_VERSION}"


# Includes in <head>
# ------------------

app_include_css = [
    versioned_asset("/assets/monocore_theme/css/workspace_fullwidth.css"),
]
app_include_js = [
    versioned_asset("/assets/monocore_theme/js/workspace_sidebar.js"),
]

boot_session = "monocore_theme.api.boot_session"

override_whitelisted_methods = {
    "frappe.desk.doctype.desktop_layout.desktop_layout.get_layout": (
        "monocore_theme.api.get_layout_with_icons"
    )
}

# Install
# -------

after_install = "monocore_theme.install.after_install"
after_migrate = "monocore_theme.install.after_install"

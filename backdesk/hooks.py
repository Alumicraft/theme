app_name = "backdesk"
app_title = "Backdesk"
app_publisher = "Backdesk"
app_description = "Backdesk workspace customizations for ERPNext"
app_email = "hello@backdesk.com"
app_license = "MIT"

BACKDESK_ASSET_VERSION = "20260601-4"


def versioned_asset(path):
    return f"{path}?v={BACKDESK_ASSET_VERSION}"


# Includes in <head>
# ------------------

app_include_css = [
    versioned_asset("/assets/backdesk/css/workspace_fullwidth.css"),
]
app_include_js = [
    versioned_asset("/assets/backdesk/js/workspace_sidebar.js"),
]

doctype_list_js = {
    "Payment Request": "public/js/payment_request_list.js",
}

boot_session = "backdesk.api.boot_session"

override_whitelisted_methods = {
    "frappe.desk.doctype.desktop_layout.desktop_layout.get_layout": (
        "backdesk.api.get_layout_with_icons"
    ),
    "frappe.desk.doctype.workspace.workspace.save_page": "backdesk.api.save_workspace_page",
}

# Install
# -------

after_install = "backdesk.install.after_install"
after_migrate = "backdesk.install.after_install"

app_name = "monocore_theme"
app_title = "Monocore Theme"
app_publisher = "Monocore"
app_description = "Custom UI theme and customizations for ERPNext"
app_email = "hello@monocore.com"
app_license = "MIT"

MONOCORE_ASSET_VERSION = "20260511-2"


def versioned_asset(path):
    return f"{path}?v={MONOCORE_ASSET_VERSION}"


# Includes in <head>
# ------------------

app_include_css = [
    "https://unpkg.com/@phosphor-icons/web@2.1.1/src/fill/style.css",
    versioned_asset("/assets/monocore_theme/css/theme.css"),
    versioned_asset("/assets/monocore_theme/css/workspace_fullwidth.css"),
]
app_include_js = [
    versioned_asset("/assets/monocore_theme/js/sidebar_icons.js"),
]

# Install
# -------

after_install = "monocore_theme.install.after_install"
after_migrate = "monocore_theme.install.after_install"

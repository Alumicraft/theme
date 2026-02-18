app_name = "monocore_theme"
app_title = "Monocore Theme"
app_publisher = "Monocore"
app_description = "Custom UI theme and customizations for ERPNext"
app_email = "hello@monocore.com"
app_license = "MIT"

# Includes in <head>
# ------------------

app_include_css = [
    "/assets/monocore_theme/css/theme.css",
    "/assets/monocore_theme/css/shortcut_group.css",
]
app_include_js = [
    "/assets/monocore_theme/js/sidebar_icons.js",
    "/assets/monocore_theme/js/shortcut_group_renderer.js",
    "/assets/monocore_theme/js/shortcut_group_block.js",
]

# Install
# -------

after_install = "monocore_theme.install.after_install"
after_migrate = "monocore_theme.install.after_install"

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text()


def test_workspace_fullwidth_css_scopes_to_workspace_shells():
    css = read("monocore_theme/public/css/workspace_fullwidth.css")

    assert 'body[data-route^="Workspaces/"]' in css
    assert "body:has(.workspace-body)" in css
    assert "--monocore-workspace-content-padding" in css
    assert ".layout-main-section-wrapper" in css
    assert ".container.page-body" in css
    assert "body.monocore-workspace-fullbleed .ce-block" not in css
    assert "body.monocore-workspace-fullbleed .widget" not in css
    assert "body.monocore-workspace-fullbleed .number-card" not in css


def test_workspace_fullwidth_css_styles_workspace_background_and_navbar_only():
    css = read("monocore_theme/public/css/workspace_fullwidth.css")

    assert "--monocore-workspace-bg" in css
    assert "--monocore-workspace-navbar-bg" in css
    assert "body.monocore-workspace-fullbleed .navbar" in css
    assert 'body[data-route^="Workspaces/"] .navbar' in css
    assert "body:has(.workspace-body) .navbar" in css
    assert 'html[data-theme="dark"] body.monocore-workspace-fullbleed' in css
    assert "body .navbar {" not in css
    assert "body .page-container {" not in css


def test_sidebar_icons_js_toggles_workspace_fullbleed_class():
    js = read("monocore_theme/public/js/sidebar_icons.js")

    assert "injectWorkspaceFullbleedStyles" in js
    assert "setWorkspaceFullbleedClass" in js
    assert "workspaceSlugFromRoute" in js
    assert "monocore-workspace-fullbleed" in js
    assert "frappe.router.on" in js
    assert "body.monocore-workspace-fullbleed .main-section" in js
    assert "--monocore-workspace-content-padding" in js


def test_hooks_include_versioned_workspace_assets():
    hooks = read("monocore_theme/hooks.py")

    assert "MONOCORE_ASSET_VERSION" in hooks
    assert "versioned_asset" in hooks
    assert 'versioned_asset("/assets/monocore_theme/css/workspace_fullwidth.css")' in hooks
    assert 'versioned_asset("/assets/monocore_theme/js/sidebar_icons.js")' in hooks


def test_pyproject_allows_erpnext_v16():
    pyproject = read("pyproject.toml")

    assert 'frappe = ">=15.0.0,<17.0.0"' in pyproject
    assert 'erpnext = ">=15.0.0,<17.0.0"' in pyproject

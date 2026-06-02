# List Route Filter Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the one-off sidebar/reportview filtering code with a small reusable rule system so future filtered Desk list links can be added by defining a rule, while preserving the current live behavior for Builds and Payment Requests.

**Architecture:** Keep clean sidebar URLs and enforced list filters as two separate responsibilities. Sidebar clicks and href cleanup use rules to remove stale/unsupported route options and present clean URLs. Reportview transport/call hooks use the same rules to append the filters that must actually be enforced.

**Tech Stack:** Frappe/ERPNext Desk client JavaScript, Backdesk hook asset versioning, pytest text/assertion tests, Chrome/in-app browser verification after an approved Frappe Cloud deploy.

---

## File Structure

```
backdesk/
  hooks.py
  public/js/workspace_sidebar.js
tests/
  test_workspace_fullwidth.py
```

No server-side API change is expected for this refactor. The existing `backdesk/api.py` Payment Request reportview override remains in place as a server-side safety net.

---

## Current Behavior To Preserve

- Builds sidebar link shows a clean URL:

```text
/desk/project/view/list?project_type=Build
```

- Builds list requests exclude completed and cancelled projects:

```js
["Project", "status", "not in", ["Completed", "Cancelled"]]
```

- Payment Requests sidebar link shows a clean URL:

```text
/desk/payment-request/view/list
```

- Payment Request list requests exclude paid requests:

```js
["Payment Request", "status", "!=", "Paid"]
```

- Existing stale Payment Request route/query filters are stripped from route options:

```text
docstatus
Payment Request.docstatus
stripe_payment_status
Payment Request.stripe_payment_status
status
Payment Request.status
```

- External URL sidebar links continue opening through Frappe's default behavior.

---

## Task 1: Add Test Coverage For A Rule Registry

**Files:**
- Modify: `tests/test_workspace_fullwidth.py`

- [ ] Add assertions that `workspace_sidebar.js` defines a reusable registry named `LIST_ROUTE_FILTER_RULES`.
- [ ] Assert the registry includes two rule ids:

```python
assert 'id: "project-builds-active"' in js
assert 'id: "payment-requests-unpaid"' in js
```

- [ ] Assert the rule data includes the current required filters:

```python
assert '["Project", "status", "not in", ["Completed", "Cancelled"]]' in js
assert '["Payment Request", "status", "!=", "Paid"]' in js
```

- [ ] Assert the rule data includes the clean route paths:

```python
assert 'clean_path: "/desk/project/view/list"' in js
assert 'clean_path: "/desk/payment-request/view/list"' in js
```

- [ ] Assert the rule data includes the clean Builds query:

```python
assert 'clean_query: { project_type: "Build" }' in js
```

- [ ] Keep the old hardcoded-function assertions for now so the test fails only after the implementation is incomplete, not because old code still exists.

- [ ] Run the focused test to see the expected failure:

```bash
python3 -m pytest tests/test_workspace_fullwidth.py -q
```

Expected: fails because `LIST_ROUTE_FILTER_RULES` does not exist yet.

---

## Task 2: Introduce The Rule Registry

**Files:**
- Modify: `backdesk/public/js/workspace_sidebar.js`

- [ ] Add this registry near the top of the closure, after the existing constants:

```js
var LIST_ROUTE_FILTER_RULES = [
	{
		id: "project-builds-active",
		doctype: "Project",
		label: "Builds",
		clean_path: "/desk/project/view/list",
		clean_query: { project_type: "Build" },
		match_route_options: {
			"Project.project_type": ["=", "Build"],
			project_type: ["=", "Build"],
		},
		strip_route_keys: [],
		force_filters: [
			["Project", "status", "not in", ["Completed", "Cancelled"]],
		],
	},
	{
		id: "payment-requests-unpaid",
		doctype: "Payment Request",
		clean_path: "/desk/payment-request/view/list",
		clean_query: {},
		match_route_options: {},
		strip_route_keys: [
			"docstatus",
			"Payment Request.docstatus",
			"stripe_payment_status",
			"Payment Request.stripe_payment_status",
			"status",
			"Payment Request.status",
		],
		force_filters: [
			["Payment Request", "status", "!=", "Paid"],
		],
	},
];
```

- [ ] Keep the registry plain JavaScript, not data fetched from the server, so it is deterministic and covered by the current asset-version deployment flow.
- [ ] Run syntax validation:

```bash
node --check backdesk/public/js/workspace_sidebar.js
```

Expected: PASS.

---

## Task 3: Replace Hardcoded Clean Href Logic With Rule Matching

**Files:**
- Modify: `backdesk/public/js/workspace_sidebar.js`
- Modify: `tests/test_workspace_fullwidth.py`

- [ ] Add helper functions below `normalize_route_options`:

```js
function values_equal(a, b) {
	return JSON.stringify(a) === JSON.stringify(b);
}

function option_matches(actual, expected) {
	var a = route_option_entry(actual);
	var e = route_option_entry(expected);
	return normalize_operator(a[0]) === normalize_operator(e[0]) && values_equal(a[1], e[1]);
}

function rule_matches_context(rule, context) {
	if (!rule || !context || context.doctype !== rule.doctype) return false;
	if (rule.label && context.label !== rule.label) return false;
	var required = rule.match_route_options || {};
	var keys = Object.keys(required);
	for (var i = 0; i < keys.length; i++) {
		var key = keys[i];
		if (context.route_options[key] !== undefined && option_matches(context.route_options[key], required[key])) {
			continue;
		}
		return false;
	}
	return true;
}

function list_filter_rule_for_context(context) {
	for (var i = 0; i < LIST_ROUTE_FILTER_RULES.length; i++) {
		if (rule_matches_context(LIST_ROUTE_FILTER_RULES[i], context)) {
			return LIST_ROUTE_FILTER_RULES[i];
		}
	}
	return null;
}

function clean_url_for_rule(rule) {
	var query = new URLSearchParams(rule.clean_query || {});
	var suffix = query.toString() ? "?" + query.toString() : "";
	return rule.clean_path + suffix;
}
```

- [ ] Update `clean_sidebar_href_for_item(item, anchor)` so it:
  - parses the route with `internal_list_route_from_anchor(anchor)`;
  - builds route options from the item/anchor using the parsed doctype;
  - finds a matching rule;
  - returns `clean_url_for_rule(rule)` when a rule exists.

Example shape:

```js
function clean_sidebar_href_for_item(item, anchor) {
	if (!item || !anchor) return null;
	try {
		var parsed = internal_list_route_from_anchor(anchor);
		if (!parsed) return null;
		var item_with_doctype = Object.assign({}, item, { link_to: parsed.doctype });
		var route_options = route_options_from_item(item_with_doctype, anchor);
		var rule = list_filter_rule_for_context({
			doctype: parsed.doctype,
			label: item.label || "",
			route_options: route_options,
		});
		return rule ? clean_url_for_rule(rule) : null;
	} catch (e) {}
	return null;
}
```

- [ ] Update tests so they no longer assert these hardcoded return statements:

```python
assert 'return "/desk/payment-request/view/list"' in js
assert 'return "/desk/project/view/list?project_type=Build"' in js
```

- [ ] Replace those with assertions for the generic helpers:

```python
assert "list_filter_rule_for_context" in js
assert "clean_url_for_rule" in js
assert "rule_matches_context" in js
```

- [ ] Run:

```bash
node --check backdesk/public/js/workspace_sidebar.js
python3 -m pytest tests/test_workspace_fullwidth.py -q
```

Expected: PASS or only failures from still-hardcoded request-filter helper assertions that will be addressed in later tasks.

---

## Task 4: Generalize Route Option Sanitization

**Files:**
- Modify: `backdesk/public/js/workspace_sidebar.js`
- Modify: `tests/test_workspace_fullwidth.py`

- [ ] Change `sanitize_list_route_options(doctype, opts)` to accept an optional context object while preserving existing call sites:

```js
function sanitize_list_route_options(doctype, opts, context) {
	if (!opts) return opts;
	var sanitized = Object.assign({}, opts);
	var rule = list_filter_rule_for_context({
		doctype: doctype,
		label: context && context.label ? context.label : "",
		route_options: sanitized,
	});
	if (rule && rule.strip_route_keys) {
		for (var i = 0; i < rule.strip_route_keys.length; i++) {
			delete sanitized[rule.strip_route_keys[i]];
		}
	}
	return sanitized;
}
```

- [ ] Update both click paths to pass the sidebar label:

```js
opts = sanitize_list_route_options(item.link_to, opts, { label: label });
opts = sanitize_list_route_options(parsed.doctype, opts, { label: label });
```

- [ ] Keep the Payment Request cleanup behavior driven by `strip_route_keys`.
- [ ] Update tests so deletion assertions point to the registry instead of direct `delete sanitized...` statements.
- [ ] Run:

```bash
node --check backdesk/public/js/workspace_sidebar.js
python3 -m pytest tests/test_workspace_fullwidth.py -q
```

Expected: PASS or only failures from request-filter helper naming.

---

## Task 5: Generalize Reportview Filter Enforcement

**Files:**
- Modify: `backdesk/public/js/workspace_sidebar.js`
- Modify: `tests/test_workspace_fullwidth.py`

- [ ] Replace the Payment Request and Project Build specific helpers with generic rule helpers:

```js
function filter_equals_expected(filter, expected) {
	var actual = normalize_reportview_filter(filter);
	var wanted = normalize_reportview_filter(expected);
	return actual &&
		wanted &&
		actual.doctype === wanted.doctype &&
		actual.field === wanted.field &&
		normalize_operator(actual.operator) === normalize_operator(wanted.operator) &&
		values_equal(actual.value, wanted.value);
}

function filters_contain_expected(filters, expected) {
	for (var i = 0; i < filters.length; i++) {
		if (filter_equals_expected(filters[i], expected)) return true;
	}
	return false;
}

function rule_matches_reportview_args(rule, args) {
	if (!rule || !args || args.doctype !== rule.doctype) return false;
	if (rule.id === "project-builds-active") {
		return has_reportview_filter(args, ["Project", "project_type", "=", "Build"]);
	}
	return true;
}

function apply_list_filter_rules_to_args(args) {
	if (!args || !args.doctype) return args;
	var filters = normalize_reportview_filters(args.filters);
	for (var i = 0; i < LIST_ROUTE_FILTER_RULES.length; i++) {
		var rule = LIST_ROUTE_FILTER_RULES[i];
		if (!rule_matches_reportview_args(rule, args)) continue;
		for (var j = 0; j < rule.force_filters.length; j++) {
			if (!filters_contain_expected(filters, rule.force_filters[j])) {
				filters.push(rule.force_filters[j]);
			}
		}
	}
	args.filters = JSON.stringify(filters);
	return args;
}
```

- [ ] Prefer a generic Project match function over `rule.id === "project-builds-active"` if it stays readable:
  - read `rule.match_route_options`;
  - translate route-option matches into reportview filter checks;
  - avoid making the helper harder to maintain than the special case it replaces.
- [ ] Rename the body/params helpers to generic names:
  - `apply_list_filter_rules_to_params(params)`
  - `apply_list_filter_rules_to_body(body)`
- [ ] Update `patch_payment_request_reportview_call` and `patch_payment_request_reportview_transport` to call the generic helpers.
- [ ] Either rename the patch functions or keep their names as compatibility wrappers. If kept, add a short comment explaining that they now patch all configured list filter rules.
- [ ] Update tests:
  - remove assertions for `force_payment_request_not_paid`;
  - remove assertions for `force_project_build_active`;
  - add assertions for `apply_list_filter_rules_to_args`;
  - add assertions for `apply_list_filter_rules_to_params`;
  - add assertions for `apply_list_filter_rules_to_body`;
  - keep assertions for the two required filter arrays.
- [ ] Run:

```bash
node --check backdesk/public/js/workspace_sidebar.js
python3 -m pytest tests/test_workspace_fullwidth.py -q
```

Expected: PASS.

---

## Task 6: Bump Asset Version

**Files:**
- Modify: `backdesk/hooks.py`
- Modify: `backdesk/public/js/workspace_sidebar.js`
- Modify: `tests/test_workspace_fullwidth.py`

- [ ] Pick the next asset version. For this implementation use:

```python
BACKDESK_ASSET_VERSION = "20260602-1"
```

- [ ] Update the client debug version to match:

```js
window.__backdesk_sidebar_debug.version = "20260602-1";
```

- [ ] Update test assertions from `20260601-11` to `20260602-1`.
- [ ] Run:

```bash
node --check backdesk/public/js/workspace_sidebar.js
python3 -m py_compile backdesk/api.py backdesk/install.py
python3 -m pytest tests/test_workspace_fullwidth.py -q
```

Expected: PASS.

---

## Task 7: Commit The Implementation

**Files:**
- Modified files from Tasks 1-6.

- [ ] Review the diff:

```bash
git diff -- backdesk/public/js/workspace_sidebar.js backdesk/hooks.py tests/test_workspace_fullwidth.py
```

- [ ] Confirm there are no unrelated changes:

```bash
git status --short
```

- [ ] Commit:

```bash
git add backdesk/public/js/workspace_sidebar.js backdesk/hooks.py tests/test_workspace_fullwidth.py
git commit -m "refactor: generalize list route filter rules"
```

Expected: commit succeeds.

---

## Task 8: Browser Verification After Explicit Deploy Approval

Do not start another Frappe Cloud deploy automatically. The prior instruction was to stop deploys after the last one, so this task requires explicit user approval before push/deploy.

After approval and Frappe Cloud deploy:

- [ ] Hard refresh Desk.
- [ ] Confirm the loaded asset contains:

```text
workspace_sidebar.js?v=20260602-1
```

- [ ] Open the Jobs workspace sidebar.
- [ ] Click Builds.
- [ ] Confirm the URL is clean:

```text
/desk/project/view/list?project_type=Build
```

- [ ] Confirm Builds excludes `Completed` and `Cancelled`.
- [ ] Click Payment Requests.
- [ ] Confirm the URL is clean:

```text
/desk/payment-request/view/list
```

- [ ] Confirm Payment Requests excludes `Paid`.
- [ ] Confirm external URL sidebar links still use Frappe's default new-tab behavior.
- [ ] Open DevTools console and confirm there are no new sidebar/reportview errors, especially:

```text
Field status is not selectable
[DCR sidebar] get_path failed
```

Expected: existing behavior still works, and adding another forced filtered list page now only requires a new `LIST_ROUTE_FILTER_RULES` entry plus focused assertions.

---

## Self-Review

- Scope stays limited to the sidebar/list-filter JavaScript and asset version tests.
- Current live behavior is preserved for Builds and Payment Requests.
- Payment Request server-side safety remains unchanged.
- The plan does not retry Frappe Workspace Route Options as the enforcement mechanism; those were unreliable for this site and can leave stale list filters.
- Deployment is explicitly gated because the latest instruction was to stop deploys after the prior deploy.

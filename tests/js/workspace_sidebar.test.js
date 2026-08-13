"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SCRIPT = fs.readFileSync(
	path.join(__dirname, "../../backdesk/public/js/workspace_sidebar.js"),
	"utf8"
);

function loadHarness(callImplementation, options = {}) {
	const counts = {
		alerts: 0,
		reloads: 0,
		routes: 0,
		routeArgs: [],
		replacements: [],
		setups: [],
		activeWorkspaceUpdates: 0,
	};
	const stored = { ...(options.stored || {}) };
	const sessionStored = { ...(options.sessionStored || {}) };
	const sidebar = {
		addEventListener() {},
		getAttribute() { return "Jobs"; },
		querySelectorAll() { return []; },
	};
	const document = {
		body: {
			classList: { toggle() {} },
			removeAttribute() {},
			setAttribute() {},
		},
		getElementById() { return {}; },
		head: { appendChild() {} },
		querySelector(selector) {
			if (selector === ".body-sidebar-container" || selector === ".body-sidebar") {
				return options.hasSidebar === false ? null : sidebar;
			}
			return null;
		},
	};
	const workspace = {
		create_page_skeleton() {},
		discard: false,
		editor: {
			save() {
				return Promise.resolve({ blocks: [{ type: "header", data: { text: "Changed" } }] });
			},
		},
		reload() { counts.reloads += 1; },
		save_page() {},
	};
	let currentRoute = options.route || ["Workspaces", "Jobs"];
	const sidebarController = {
		current_workspace: options.currentWorkspace || "Jobs",
		set_active_workspace_item() { counts.activeWorkspaceUpdates += 1; },
		set_workspace_sidebar() {},
		setup(workspaceTitle) {
			counts.setups.push(workspaceTitle);
			this.current_workspace = workspaceTitle;
			this.sidebar_title = workspaceTitle;
		},
		sidebar_title: options.currentWorkspace || "Jobs",
	};
	if (options.legacySidebarPatch) {
		sidebarController._sidebar_fix_original_setup = sidebarController.setup.bind(sidebarController);
		sidebarController.setup = function legacySetup(workspaceTitle) {
			return this._sidebar_fix_original_setup(workspaceTitle);
		};
	}
	const frappe = {
		app: {
			sidebar: sidebarController,
		},
		boot: {
			workspace_sidebar_item: Object.fromEntries(
				["Overview", "Jobs", "Products", "Finance", "Contacts", "Access", "Terminal", "Selling"]
					.map((label) => [label.toLowerCase(), { label, items: [] }])
			),
		},
		call: callImplementation,
		get_route() { return currentRoute; },
		router: { on() {}, slug(value) { return value.toLowerCase(); } },
		route_flags: {},
		set_route(...args) {
			counts.routes += 1;
			counts.routeArgs.push(args);
			return Promise.resolve();
		},
		show_alert() { counts.alerts += 1; },
		ui: {},
		workspace,
	};
	const jquery = function () {
		return {
			on() {},
			ready(callback) { callback(); },
		};
	};
	const context = {
		MutationObserver: class { observe() {} },
		URL,
		URLSearchParams,
		__: (value) => value,
		console,
		document,
		frappe,
		localStorage: {
			getItem(key) { return stored[key] ?? null; },
			setItem(key, value) { stored[key] = value; },
		},
		sessionStorage: {
			getItem(key) { return sessionStored[key] ?? null; },
			setItem(key, value) { sessionStored[key] = value; },
		},
		setInterval() { return 1; },
		clearInterval() {},
		setTimeout() { return 1; },
		window: {
			Cypress: false,
			location: {
				origin: "https://example.test",
				pathname: options.pathname || "/desk/jobs",
				replace(pathname) { counts.replacements.push(pathname); },
			},
		},
		$: jquery,
	};
	context.window.window = context.window;
	context.window.document = document;
	context.window.frappe = frappe;
	context.window.$ = jquery;
	vm.runInNewContext(SCRIPT, context);
	return {
		counts,
		frappe,
		workspace,
		stored,
		sessionStored,
		setRoute(route) { currentRoute = route; },
	};
}

test("workspace save completes once when Frappe uses callback and Promise", async () => {
	let callback;
	const response = { message: { name: "Jobs" } };
	const harness = loadHarness((options) => {
		callback = options.callback;
		callback(response);
		return Promise.resolve(response);
	});

	const saved = await harness.workspace.save_page({
		content: "[]",
		name: "Jobs",
		public: 1,
	});
	await Promise.resolve();

	assert.equal(saved, true);
	assert.equal(harness.counts.reloads, 1);
	assert.equal(harness.counts.alerts, 1);
	assert.equal(harness.counts.routes, 1);
});

test("bare Desk route restores the last Alumicraft workspace with SPA history replacement", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["desk"],
		pathname: "/desk",
		hasSidebar: false,
		stored: { backdesk_sidebar_fix_last_workspace: "Jobs" },
	});

	assert.deepEqual(harness.counts.replacements, []);
	assert.equal(JSON.stringify(harness.counts.routeArgs), JSON.stringify([[["jobs"]]]));
	assert.equal(harness.frappe.route_flags.replace_route, true);
});

test("bare Desk route prefers the tab workspace over another tab's global workspace", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["desk"],
		pathname: "/desk",
		hasSidebar: false,
		stored: { backdesk_sidebar_fix_last_workspace: "Jobs" },
		sessionStored: { backdesk_sidebar_fix_tab_workspace: "Finance" },
	});

	assert.deepEqual(harness.counts.replacements, []);
	assert.equal(JSON.stringify(harness.counts.routeArgs), JSON.stringify([[["finance"]]]));
});

test("concrete Desk route is preserved while Frappe boot route is temporarily empty", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: [],
		pathname: "/desk/quickbook-settings/Quickbook%20Settings",
		hasSidebar: false,
		stored: { backdesk_sidebar_fix_last_workspace: "Jobs" },
	});

	assert.deepEqual(harness.counts.replacements, []);
});

test("stock Selling workspace is replaced by the last Alumicraft workspace", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["Workspaces", "Selling"],
		pathname: "/desk/selling",
		stored: { backdesk_sidebar_fix_last_workspace: "Finance" },
	});

	assert.deepEqual(harness.counts.replacements, []);
	assert.equal(JSON.stringify(harness.counts.routeArgs), JSON.stringify([[["finance"]]]));
});

test("stock workspace cannot become the remembered Alumicraft workspace", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["Workspaces", "Selling"],
		pathname: "/desk/selling",
		currentWorkspace: "Selling",
		stored: { backdesk_sidebar_fix_last_workspace: "Selling" },
	});

	assert.deepEqual(harness.counts.replacements, []);
	assert.equal(JSON.stringify(harness.counts.routeArgs), JSON.stringify([[["overview"]]]));
});

test("valid Alumicraft workspace stays on its current route", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["Workspaces", "Finance"],
		pathname: "/desk/finance",
	});

	assert.deepEqual(harness.counts.replacements, []);
});

test("workspace switch remains interactive across repeated navigation with legacy patch loaded", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["Workspaces", "Jobs"],
		currentWorkspace: "Jobs",
		legacySidebarPatch: true,
	});

	harness.setRoute(["Workspaces", "Finance"]);
	harness.frappe.app.sidebar.set_workspace_sidebar();
	harness.setRoute(["Workspaces", "Overview"]);
	harness.frappe.app.sidebar.set_workspace_sidebar();
	harness.setRoute(["Workspaces", "Jobs"]);
	harness.frappe.app.sidebar.set_workspace_sidebar();

	assert.deepEqual(harness.counts.setups, ["Finance", "Overview", "Jobs"]);
	assert.equal(harness.frappe.app.sidebar.sidebar_title, "Jobs");
	assert.equal(harness.sessionStored.backdesk_sidebar_fix_tab_workspace, "Jobs");
	assert.equal(harness.counts.activeWorkspaceUpdates, 3);
});

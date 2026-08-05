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
	const counts = { alerts: 0, reloads: 0, routes: 0, replacements: [] };
	const stored = { ...(options.stored || {}) };
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
				return sidebar;
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
	const frappe = {
		app: {
			sidebar: {
				current_workspace: options.currentWorkspace || "Jobs",
				set_active_workspace_item() {},
				set_workspace_sidebar() {},
				setup() {},
				sidebar_title: options.currentWorkspace || "Jobs",
			},
		},
		boot: {
			workspace_sidebar_item: Object.fromEntries(
				["Overview", "Jobs", "Products", "Finance", "Contacts", "Access", "Terminal", "Selling"]
					.map((label) => [label.toLowerCase(), { label, items: [] }])
			),
		},
		call: callImplementation,
		get_route() { return options.route || ["Workspaces", "Jobs"]; },
		router: { on() {}, slug(value) { return value.toLowerCase(); } },
		set_route() { counts.routes += 1; },
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
	return { counts, frappe, workspace, stored };
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

test("bare Desk route restores the last Alumicraft workspace with history replacement", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: [],
		pathname: "/desk",
		stored: { backdesk_sidebar_fix_last_workspace: "Jobs" },
	});

	assert.deepEqual(harness.counts.replacements, ["/desk/jobs"]);
});

test("stock Selling workspace is replaced by the last Alumicraft workspace", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["Workspaces", "Selling"],
		pathname: "/desk/selling",
		stored: { backdesk_sidebar_fix_last_workspace: "Finance" },
	});

	assert.deepEqual(harness.counts.replacements, ["/desk/finance"]);
});

test("stock workspace cannot become the remembered Alumicraft workspace", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["Workspaces", "Selling"],
		pathname: "/desk/selling",
		currentWorkspace: "Selling",
		stored: { backdesk_sidebar_fix_last_workspace: "Selling" },
	});

	assert.deepEqual(harness.counts.replacements, ["/desk/overview"]);
});

test("valid Alumicraft workspace stays on its current route", () => {
	const harness = loadHarness(() => Promise.resolve({}), {
		route: ["Workspaces", "Finance"],
		pathname: "/desk/finance",
	});

	assert.deepEqual(harness.counts.replacements, []);
});

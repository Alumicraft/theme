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

function loadHarness(callImplementation) {
	const counts = { alerts: 0, reloads: 0, routes: 0 };
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
				current_workspace: "Jobs",
				set_active_workspace_item() {},
				set_workspace_sidebar() {},
				setup() {},
				sidebar_title: "Jobs",
			},
		},
		boot: { workspace_sidebar_item: {} },
		call: callImplementation,
		get_route() { return ["Workspaces", "Jobs"]; },
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
		localStorage: { getItem() { return null; }, setItem() {} },
		setInterval() { return 1; },
		clearInterval() {},
		setTimeout() { return 1; },
		window: { Cypress: false, location: { origin: "https://example.test" } },
		$: jquery,
	};
	context.window.window = context.window;
	context.window.document = document;
	context.window.frappe = frappe;
	context.window.$ = jquery;
	vm.runInNewContext(SCRIPT, context);
	return { counts, frappe, workspace };
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


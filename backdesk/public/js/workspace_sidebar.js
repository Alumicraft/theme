/**
 * Backdesk workspace/sidebar fixes for Frappe v15/v16 Desk.
 *
 * Keeps filtered sidebar navigation, duplicate DocType active states, and
 * workspace selection stable across List/Form route changes.
 */
(function () {
	"use strict";

	window.__backdesk_sidebar_debug = window.__backdesk_sidebar_debug || {};
	window.__backdesk_sidebar_debug.version = "20260601-7";

	var _initialized = false;
	var _last_clicked = null;
	var ENTITY_WORKSPACE_PREFIX = "backdesk_workspace_for_";
	var DOCTYPE_MAP_KEY = "backdesk_sidebar_fix_doctype_workspace";
	var GLOBAL_KEY = "backdesk_sidebar_fix_last_workspace";

	function parse_filters(str) {
		if (!str) return [];
		if (Array.isArray(str)) return str;
		if (typeof str === "object") return [str];
		try {
			var r = JSON.parse(str);
			return Array.isArray(r) ? r : [];
		} catch (e) {
			return [];
		}
	}

	function fieldname_from_label(field) {
		return (field || "")
			.toString()
			.trim()
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "_")
			.replace(/^_+|_+$/g, "");
	}

	function normalize_operator(operator) {
		var op = (operator || "=").toString();
		var lower = op.toLowerCase();
		if (lower === "equals" || lower === "==" || lower === "=") return "=";
		if (lower === "not equals") return "!=";
		return op;
	}

	function filter_parts(f) {
		if (!f) return null;
		if (Array.isArray(f)) {
			if (f.length >= 4) {
				return {
					doctype: (f[0] || "").toString().trim(),
					field: (f[1] || "").toString().trim(),
					operator: normalize_operator(f[2]),
					value: f[3],
				};
			}
			if (f.length === 3) {
				return {
					doctype: "",
					field: (f[0] || "").toString().trim(),
					operator: normalize_operator(f[1]),
					value: f[2],
				};
			}
			if (f.length === 2) {
				return {
					doctype: "",
					field: (f[0] || "").toString().trim(),
					operator: "=",
					value: f[1],
				};
			}
			return null;
		}
		if (typeof f === "object") {
			return {
				doctype: (f.doctype || f.dt || f.document_type || "").toString().trim(),
				field: (
					f.fieldname ||
					f.field ||
					f.field_name ||
					fieldname_from_label(f.label)
				).toString().trim(),
				operator: normalize_operator(f.operator || f.condition || f.op),
				value: f.value != null ? f.value : f.filter_value,
			};
		}
		return null;
	}

	function filters_to_route_options(filters) {
		var opts = {};
		for (var i = 0; i < filters.length; i++) {
			var parts = filter_parts(filters[i]);
			if (!parts || !parts.field || parts.value == null || parts.value === "") continue;
			var key = parts.doctype ? parts.doctype + "." + parts.field : parts.field;
			var entry = [parts.operator, parts.value];
			if (opts[key] === undefined) {
				opts[key] = entry;
			} else if (Array.isArray(opts[key]) && Array.isArray(opts[key][0])) {
				opts[key].push(entry);
			} else {
				opts[key] = [opts[key], entry];
			}
		}
		return opts;
	}

	function route_option_key(key, item) {
		key = (key || "").toString().trim();
		if (key && key.indexOf(".") === -1 && item && item.link_to) {
			return item.link_to + "." + key;
		}
		return key;
	}

	function route_option_entry(value) {
		var v = value;
		if (typeof v === "string") {
			try {
				v = JSON.parse(v);
			} catch (e) {}
		}
		if (Array.isArray(v)) return v;
		return ["=", v];
	}

	function normalize_route_options(raw, item) {
		var opts = {};
		if (!raw || typeof raw !== "object") return opts;
		Object.keys(raw).forEach(function (key) {
			var normalized_key = route_option_key(key, item);
			var entry = route_option_entry(raw[key]);
			if (!normalized_key || entry[1] == null || entry[1] === "") return;
			opts[normalized_key] = entry;
		});
		return opts;
	}

	function route_options_from_anchor(anchor, item) {
		var opts = {};
		if (!anchor || !anchor.search) return opts;
		try {
			var params = new URLSearchParams(anchor.search);
			params.forEach(function (value, key) {
				var normalized_key = route_option_key(key, item);
				var entry = route_option_entry(value);
				if (!normalized_key || entry[1] == null || entry[1] === "") return;
				opts[normalized_key] = entry;
			});
		} catch (e) {}
		return opts;
	}

	function route_options_from_url(raw_url, item) {
		var opts = {};
		if (!raw_url) return opts;
		try {
			var url = new URL(raw_url, window.location.origin);
			if (!url.search) return opts;
			var params = new URLSearchParams(url.search);
			params.forEach(function (value, key) {
				var normalized_key = route_option_key(key, item);
				var entry = route_option_entry(value);
				if (!normalized_key || entry[1] == null || entry[1] === "") return;
				opts[normalized_key] = entry;
			});
		} catch (e) {}
		return opts;
	}

	function route_options_from_item(item, anchor) {
		var url_opts = route_options_from_url(item.url, item);
		if (Object.keys(url_opts).length) return url_opts;
		var opts = filters_to_route_options(parse_filters(item.filters));
		if (Object.keys(opts).length) return opts;
		if (item.route_options) {
			var raw = item.route_options;
			if (typeof raw === "string") {
				try {
					raw = JSON.parse(raw);
				} catch (e) {
					raw = null;
				}
			}
			opts = normalize_route_options(raw, item);
			if (Object.keys(opts).length) return opts;
		}
		return route_options_from_anchor(anchor, item);
	}

	function sanitize_list_route_options(doctype, opts) {
		if (doctype !== "Payment Request" || !opts) return opts;
		var sanitized = Object.assign({}, opts);
		delete sanitized.status;
		delete sanitized["Payment Request.status"];
		return sanitized;
	}

	function list_view_for_item(item, anchor) {
		if (item && item.tab) return item.tab;
		if (anchor && anchor.pathname) {
			var match = anchor.pathname.match(/\/view\/([^/?#]+)/);
			if (match && match[1]) {
				return match[1].charAt(0).toUpperCase() + match[1].slice(1);
			}
		}
		return "List";
	}

	function doctype_from_route_segment(segment) {
		return (segment || "")
			.toString()
			.split("-")
			.filter(Boolean)
			.map(function (part) {
				return part.charAt(0).toUpperCase() + part.slice(1);
			})
			.join(" ");
	}

	function internal_list_route_from_anchor(anchor) {
		if (!anchor) return null;
		try {
			var href = anchor.getAttribute("href") || anchor.href;
			if (!href) return null;
			var url = new URL(href, window.location.origin);
			if (url.origin !== window.location.origin) return null;
			var match = url.pathname.match(/^\/(?:desk|app)\/([^/?#]+)\/view\/([^/?#]+)/);
			if (!match || !match[1] || !match[2]) return null;
			return {
				doctype: doctype_from_route_segment(decodeURIComponent(match[1])),
				view: match[2].charAt(0).toUpperCase() + match[2].slice(1),
			};
		} catch (e) {
			return null;
		}
	}

	function normalize(s) {
		return (s || "").toLowerCase().replace(/[\s_-]+/g, "");
	}

	function slugify(s) {
		return (s || "")
			.toLowerCase()
			.replace(/[\s_]+/g, "-")
			.replace(/[^a-z0-9-]/g, "")
			.replace(/-+/g, "-")
			.replace(/^-|-$/g, "");
	}

	function workspace_from_slug(slug) {
		var map = frappe.boot.workspace_sidebar_item || {};
		var target = slugify(slug);
		if (!target) return null;
		if (map[slug]) return { key: slug, label: map[slug].label || slug, data: map[slug] };
		if (map[target]) return { key: target, label: map[target].label || target, data: map[target] };
		var keys = Object.keys(map);
		for (var i = 0; i < keys.length; i++) {
			var key = keys[i];
			var data = map[key] || {};
			if (slugify(key) === target || slugify(data.label) === target) {
				return { key: key, label: data.label || key, data: data };
			}
		}
		return null;
	}

	function candidate_label(label, candidates) {
		var workspace = workspace_from_slug(label);
		var target = normalize(workspace ? workspace.label : label);
		if (!target) return null;
		for (var i = 0; i < candidates.length; i++) {
			if (normalize(candidates[i]) === target) return candidates[i];
		}
		return null;
	}

	function get_workspace_for_entity(entity, candidates) {
		try {
			return candidate_label(
				localStorage.getItem(ENTITY_WORKSPACE_PREFIX + normalize(entity)),
				candidates
			);
		} catch (e) {
			return null;
		}
	}

	function read_doctype_map() {
		try {
			var raw = localStorage.getItem(DOCTYPE_MAP_KEY);
			if (!raw) return {};
			var parsed = JSON.parse(raw);
			return parsed && typeof parsed === "object" ? parsed : {};
		} catch (e) {
			return {};
		}
	}

	function remember_workspace_for_entity(entity, workspace_name) {
		var workspace = workspace_from_slug(workspace_name);
		if (!entity || !workspace) return false;
		try {
			localStorage.setItem(ENTITY_WORKSPACE_PREFIX + normalize(entity), workspace.label);
			localStorage.setItem(GLOBAL_KEY, workspace.label);
			return true;
		} catch (e) {
			return false;
		}
	}

	function remember_doctype_workspace(doctype) {
		if (!doctype) return false;
		var workspace = workspace_from_slug(get_workspace_name());
		if (!workspace) return false;
		try {
			var map = read_doctype_map();
			map[doctype] = workspace.label;
			map[normalize(doctype)] = workspace.label;
			localStorage.setItem(DOCTYPE_MAP_KEY, JSON.stringify(map));
			localStorage.setItem(GLOBAL_KEY, workspace.label);
			return true;
		} catch (e) {
			return false;
		}
	}

	function get_workspace_name() {
		if (frappe.app && frappe.app.sidebar && frappe.app.sidebar.current_workspace) {
			return frappe.app.sidebar.current_workspace;
		}
		if (frappe.app && frappe.app.sidebar && frappe.app.sidebar.sidebar_title) {
			return frappe.app.sidebar.sidebar_title;
		}
		var el = document.querySelector(".body-sidebar[data-title]");
		if (el) return el.getAttribute("data-title");
		return null;
	}

	function flatten_items(items, out) {
		for (var i = 0; i < items.length; i++) {
			var item = items[i];
			out.push(item);
			flatten_items(item.nested_items || [], out);
		}
	}

	function get_all_items() {
		var ws = get_workspace_name();
		if (!ws) return [];
		var workspace = workspace_from_slug(ws);
		var data = workspace && workspace.data;
		var all = [];
		if (data && data.items) flatten_items(data.items, all);
		return all;
	}

	function set_active(container) {
		var sb = document.querySelector(".body-sidebar-container");
		if (!sb) return;
		var all = sb.querySelectorAll(".standard-sidebar-item");
		for (var i = 0; i < all.length; i++) all[i].classList.remove("active-sidebar");
		var target = container.querySelector(".standard-sidebar-item") || container;
		target.classList.add("active-sidebar");
	}

	function find_dom_by_label(label) {
		var sb = document.querySelector(".body-sidebar-container");
		if (!sb) return null;
		var els = sb.querySelectorAll(".sidebar-item-container");
		for (var i = 0; i < els.length; i++) {
			var lbl = els[i].querySelector(".sidebar-item-label");
			if (lbl && lbl.textContent.trim() === label) return els[i];
		}
		return null;
	}

	function track_click(label, item) {
		_last_clicked = { label: label, link_to: item.link_to };
		var attempts = 0;
		var poll = setInterval(function () {
			attempts++;
			if (attempts > 25 || !_last_clicked) {
				clearInterval(poll);
				return;
			}
			var el = find_dom_by_label(_last_clicked.label);
			if (!el) return;
			var inner = el.querySelector(".standard-sidebar-item");
			if (inner && !inner.classList.contains("active-sidebar")) set_active(el);
		}, 200);
		setTimeout(function () {
			_last_clicked = null;
		}, 5000);
	}

	function on_click(e) {
		var container = e.target.closest(".sidebar-item-container");
		if (!container) return;
		var lbl_el = container.querySelector(".sidebar-item-label");
		if (!lbl_el) return;
		var label = lbl_el.textContent.trim();

		var items = get_all_items();
		var item = null;
		for (var i = 0; i < items.length; i++) {
			if (items[i].label === label) {
				item = items[i];
				break;
			}
		}
		if (!item || item.type !== "Link") return;
		var anchor = e.target.closest("a.item-anchor") || e.target.closest("a") || container.querySelector("a");
		remember_workspace_for_entity(item.link_to, get_workspace_name());
		remember_doctype_workspace(item.link_to);

		var opts = route_options_from_item(item, anchor);
		if (item.link_to && (item.link_type === "DocType" || !item.link_type) && Object.keys(opts).length) {
			e.preventDefault();
			e.stopPropagation();
			if (e.stopImmediatePropagation) e.stopImmediatePropagation();
			var view = list_view_for_item(item, anchor);
			opts = sanitize_list_route_options(item.link_to, opts);
			frappe.route_options = opts;
			track_click(label, item);
			window.__backdesk_sidebar_debug.lastClick = {
				label: label,
				link_to: item.link_to,
				view: view,
				opts: opts,
			};
			frappe.set_route(["List", item.link_to, view]);
			return;
		}

		var parsed = internal_list_route_from_anchor(anchor);
		if (item.link_type === "URL" && parsed) {
			opts = route_options_from_item(
				Object.assign({}, item, {
					link_to: parsed.doctype,
				}),
				anchor
			);
			e.preventDefault();
			e.stopPropagation();
			if (e.stopImmediatePropagation) e.stopImmediatePropagation();
			opts = sanitize_list_route_options(parsed.doctype, opts);
			frappe.route_options = opts;
			track_click(label, {
				link_to: parsed.doctype,
			});
			window.__backdesk_sidebar_debug.lastUrlClick = {
				label: label,
				doctype: parsed.doctype,
				view: parsed.view,
				opts: opts,
			};
			frappe.set_route(["List", parsed.doctype, parsed.view]);
			return;
		}

		track_click(label, item);
	}

	function fix_active() {
		if (_last_clicked) {
			var dt = typeof cur_list !== "undefined" && cur_list ? cur_list.doctype : null;
			if (dt && dt === _last_clicked.link_to) {
				var clicked = find_dom_by_label(_last_clicked.label);
				if (clicked) {
					set_active(clicked);
					return;
				}
			}
			_last_clicked = null;
		}

		if (typeof cur_list === "undefined" || !cur_list || !cur_list.doctype) return;
		var items = get_all_items();
		var matches = [];
		for (var i = 0; i < items.length; i++) {
			if (items[i].type === "Link" && items[i].link_to === cur_list.doctype) matches.push(items[i]);
		}
		if (matches.length <= 1) return;

		var cur_filters = [];
		try {
			cur_filters = cur_list.filter_area.get();
		} catch (e) {
			return;
		}

		var best = null;
		var best_score = -1;
		for (var j = 0; j < matches.length; j++) {
			var mf = parse_filters(matches[j].filters);
			if (!mf.length && !cur_filters.length) {
				if (0 > best_score) {
					best_score = 0;
					best = matches[j];
				}
				continue;
			}
			if (!mf.length) continue;
			var score = 0;
			var ok = true;
			for (var k = 0; k < mf.length; k++) {
				var f = filter_parts(mf[k]);
				var found = false;
				if (!f) continue;
				for (var m = 0; m < cur_filters.length; m++) {
					var cf = filter_parts(cur_filters[m]);
					if (cf && cf.field === f.field && cf.operator === f.operator && String(cf.value) === String(f.value)) {
						found = true;
						break;
					}
				}
				if (found) score++;
				else {
					ok = false;
					break;
				}
			}
			if (ok && score > best_score) {
				best_score = score;
				best = matches[j];
			}
		}
		if (best) {
			var el = find_dom_by_label(best.label);
			if (el) set_active(el);
		}
	}

	function fix_active_retry(n) {
		if (n <= 0) return;
		if (typeof cur_list !== "undefined" && cur_list && cur_list.filter_area) fix_active();
		else setTimeout(function () { fix_active_retry(n - 1); }, 200);
	}

	function workspace_slug_from_route(route) {
		if (!route || !route.length) return null;
		if (route.length === 1 && route[0] && workspace_from_slug(route[0])) return route[0].toLowerCase();
		if (route.length >= 2 && (route[0] || "").toLowerCase() === "workspaces" && route[1]) {
			if ((route[1] || "").toLowerCase() === "private" && route[2]) return route[2].toLowerCase();
			return route[1].toLowerCase();
		}
		return null;
	}

	function find_candidate_workspaces(entity) {
		var map = frappe.boot.workspace_sidebar_item || {};
		var out = [];
		var target = normalize(entity);
		Object.keys(map).forEach(function (key) {
			var data = map[key];
			if (!data || !data.items) return;
			var all = [];
			flatten_items(data.items, all);
			for (var i = 0; i < all.length; i++) {
				if (all[i] && normalize(all[i].link_to) === target) {
					out.push(data.label || key);
					return;
				}
			}
		});
		return out;
	}

	function pick_correct_workspace() {
		try {
			var route = frappe.get_route() || [];
			var ws_slug = workspace_slug_from_route(route);
			if (ws_slug && workspace_from_slug(ws_slug)) return null;

			var entity = null;
			if (route.length >= 2) entity = route[1];
			else if (route.length === 1) entity = route[0];
			if (!entity) return null;

			var candidates = find_candidate_workspaces(entity);
			if (!candidates.length) return null;
			if (candidates.length === 1) return candidates[0];

			var doctype_map = read_doctype_map();
			var doctype_workspace = candidate_label(doctype_map[entity] || doctype_map[normalize(entity)], candidates);
			if (doctype_workspace) return doctype_workspace;

			var entity_workspace = get_workspace_for_entity(entity, candidates);
			if (entity_workspace) return entity_workspace;

			var last = null;
			try {
				last = localStorage.getItem(GLOBAL_KEY);
			} catch (e) {}
			var last_workspace = candidate_label(last, candidates);
			if (last_workspace) return last_workspace;
			return candidates[0];
		} catch (e) {
			return null;
		}
	}

	function save_last_workspace() {
		try {
			var route = frappe.get_route() || [];
			var slug = workspace_slug_from_route(route);
			if (!slug) return false;
			var workspace = workspace_from_slug(slug);
			if (!workspace) return false;
			localStorage.setItem(GLOBAL_KEY, workspace.label);
			return true;
		} catch (e) {
			return false;
		}
	}

	function enforce_correct_workspace() {
		if (!frappe.app || !frappe.app.sidebar) return;
		var sb = frappe.app.sidebar;
		var correct = pick_correct_workspace();
		if (!correct || sb.sidebar_title === correct) return;
		var setup = sb._backdesk_original_setup;
		if (typeof setup !== "function" && typeof sb.setup === "function") setup = sb.setup.bind(sb);
		if (typeof setup !== "function") return;
		try {
			setup(correct);
		} catch (e) {}
	}

	function patch_workspace_switch() {
		if (!frappe.app || !frappe.app.sidebar) return false;
		var sb = frappe.app.sidebar;
		if (sb._backdesk_workspace_patched) return true;
		if (typeof sb.set_workspace_sidebar !== "function") return false;
		if (typeof sb.setup !== "function") return false;

		var original = sb.set_workspace_sidebar.bind(sb);
		var original_setup = sb.setup.bind(sb);

		sb.set_workspace_sidebar = function (router) {
			try {
				var route = frappe.get_route() || [];
				var slug = "";
				if (route.length === 1) {
					slug = (route[0] || "").toLowerCase();
				} else if (route.length >= 2 && (route[0] || "").toLowerCase() === "workspaces") {
					return original(router);
				}

				var is_workspace_nav = slug && !!workspace_from_slug(slug);
				var correct = pick_correct_workspace();
				if (!is_workspace_nav && correct) {
					if (sb.sidebar_title !== correct) {
						original_setup(correct);
					} else if (typeof sb.set_active_workspace_item === "function") {
						sb.set_active_workspace_item();
					}
					return;
				}

				if (is_workspace_nav || !sb.sidebar_title) return original(router);
				sb.set_active_workspace_item();
			} catch (e) {
				return original(router);
			}
		};

		sb.setup = function (workspace_title) {
			try {
				var route = frappe.get_route() || [];
				var is_doctype_view =
					route.indexOf("List") !== -1 ||
					route.indexOf("Form") !== -1 ||
					route.indexOf("query-report") !== -1 ||
					route.indexOf("dashboard-view") !== -1 ||
					route.indexOf("Tree") !== -1;

				if (is_doctype_view) {
					var correct = pick_correct_workspace();
					if (correct && workspace_title !== correct) {
						original_setup(correct);
						return;
					}
					if (sb.sidebar_title && workspace_title !== sb.sidebar_title) {
						if (typeof sb.set_active_workspace_item === "function") sb.set_active_workspace_item();
						return;
					}
				}
			} catch (e) {}
			return original_setup(workspace_title);
		};

		sb._backdesk_workspace_patched = true;
		sb._backdesk_original_setup = original_setup;
		return true;
	}

	function try_patch_workspace_switch(n) {
		if (n <= 0) return;
		if (!patch_workspace_switch()) setTimeout(function () { try_patch_workspace_switch(n - 1); }, 300);
	}

	function patch_workspace_save_page() {
		try {
			if (!frappe.workspace || typeof frappe.workspace.save_page !== "function") return false;
			var ws = frappe.workspace;
			if (ws._backdesk_save_page_patched) return true;

			ws.save_page = function (page) {
				var workspace = this;
				workspace.current_page = { name: page.name, public: page.public };

				return workspace.editor.save().then(function (output) {
					var new_widgets = {};
					output.blocks.forEach(function (block) {
						if (!block.data.new) return;
						if (!new_widgets[block.type]) new_widgets[block.type] = [];
						new_widgets[block.type].push(block.data.new);
						delete block.data.new;
					});

					var blocks = output.blocks.filter(function (block) {
						return (
							block.type !== "card" ||
							(block.data.card_name !== "Custom Documents" && block.data.card_name !== "Custom Reports")
						);
					});
					var content = JSON.stringify(blocks);
					var current_content = typeof page.content === "string" ? page.content : JSON.stringify(page.content || []);
					if (current_content === content && Object.keys(new_widgets).length === 0) {
						frappe.show_alert({ message: __("No changes made"), indicator: "warning" });
						return true;
					}

					workspace.create_page_skeleton();
					page.content = content;

					return new Promise(function (resolve) {
						var completed = false;
						function finish(saved) {
							if (completed) return;
							completed = true;
							resolve(saved);
						}

						function handle_success(response) {
							if (response && response.exc) {
								workspace.reload();
								finish(false);
								return;
							}

							workspace.discard = true;
							workspace.reload();
							if (!window.Cypress) {
								frappe.show_alert({ message: __("Saved"), indicator: "green" });
								if (page.public) frappe.set_route("desk", frappe.router.slug(page.name));
								else frappe.set_route("desk", "private", frappe.router.slug(page.name));
							}
							finish(true);
						}

						var request = frappe.call({
							method: "backdesk.api.save_workspace_page",
							args: {
								name: page.name,
								public: page.public || 0,
								new_widgets: new_widgets,
								blocks: content,
							},
							callback: handle_success,
							error: function () {
								workspace.reload();
								finish(false);
							},
						});
						if (request && typeof request.then === "function") {
							request.then(handle_success).catch(function () {
								workspace.reload();
								finish(false);
							});
						}
					});
				}).catch(function () {
					return false;
				});
			};

			ws._backdesk_save_page_patched = true;
			return true;
		} catch (e) {
			return false;
		}
	}

	function try_patch_workspace_save_page(n) {
		if (n <= 0) return;
		if (!patch_workspace_save_page()) setTimeout(function () { try_patch_workspace_save_page(n - 1); }, 300);
	}

	function patch_typelink_get_path() {
		try {
			if (!frappe.ui || !frappe.ui.sidebar_item || !frappe.ui.sidebar_item.TypeLink) return false;
			var proto = frappe.ui.sidebar_item.TypeLink.prototype;
			if (proto._backdesk_sidebar_fix_get_path_patched) return true;
			var original = proto.get_path;
			if (typeof original !== "function") return false;
			proto.get_path = function () {
				try {
					return original.call(this);
				} catch (e) {
					return null;
				}
			};
			proto._backdesk_sidebar_fix_get_path_patched = true;
			return true;
		} catch (e) {
			return false;
		}
	}

	function try_patch_typelink_get_path(n) {
		if (n <= 0) return;
		if (!patch_typelink_get_path()) setTimeout(function () { try_patch_typelink_get_path(n - 1); }, 300);
	}

	function try_watch_sidebar_title(n) {
		if (n <= 0) return;
		var el = document.querySelector(".body-sidebar");
		if (!el) {
			setTimeout(function () { try_watch_sidebar_title(n - 1); }, 300);
			return;
		}
		if (el._backdesk_title_watched) return;
		el._backdesk_title_watched = true;

		var reverting = false;
		var observer = new MutationObserver(function () {
			if (reverting) return;
			var current = el.getAttribute("data-title");
			var correct = pick_correct_workspace();
			if (!correct || current === correct) return;
			reverting = true;
			enforce_correct_workspace();
			setTimeout(function () { reverting = false; }, 100);
		});
		observer.observe(el, { attributes: true, attributeFilter: ["data-title"] });
	}

	function normalize_reportview_filters(filters) {
		if (!filters) return [];
		if (typeof filters === "string") {
			try {
				filters = JSON.parse(filters);
			} catch (e) {
				filters = [];
			}
		}
		if (Array.isArray(filters)) return filters.slice();
		if (typeof filters !== "object") return [];

		return Object.keys(filters).map(function (fieldname) {
			var value = filters[fieldname];
			if (
				Array.isArray(value) &&
				value.length &&
				["=", ">", "<", ">=", "<=", "!=", "like", "not like", "in", "not in", "between", "is"].indexOf(
					(value[0] || "").toString().toLowerCase()
				) !== -1
			) {
				return [fieldname, value[0], value.length > 1 ? value[1] : null];
			}
			return [fieldname, "=", value];
		});
	}

	function has_payment_request_not_paid_filter(filters) {
		for (var i = 0; i < filters.length; i++) {
			var condition = filters[i];
			if (!Array.isArray(condition)) continue;
			if (condition.length >= 4) {
				if (
					condition[0] === "Payment Request" &&
					condition[1] === "status" &&
					condition[2] === "!=" &&
					condition[3] === "Paid"
				) {
					return true;
				}
			} else if (condition.length >= 3) {
				if (condition[0] === "status" && condition[1] === "!=" && condition[2] === "Paid") {
					return true;
				}
			}
		}
		return false;
	}

	function force_payment_request_not_paid(args) {
		if (!args || args.doctype !== "Payment Request") return;
		var filters = normalize_reportview_filters(args.filters);
		if (!has_payment_request_not_paid_filter(filters)) {
			filters.push(["Payment Request", "status", "!=", "Paid"]);
		}
		args.filters = JSON.stringify(filters);
	}

	function force_payment_request_not_paid_params(params) {
		if (!params || params.get("doctype") !== "Payment Request") return false;
		var filters = normalize_reportview_filters(params.get("filters"));
		if (!has_payment_request_not_paid_filter(filters)) {
			filters.push(["Payment Request", "status", "!=", "Paid"]);
		}
		params.set("filters", JSON.stringify(filters));
		return true;
	}

	function reportview_url(url) {
		return /(?:^|\/)api\/method\/frappe\.desk\.reportview\.(?:get|get_count|get_list)(?:[?#]|$)/.test(
			(url || "").toString()
		);
	}

	function force_payment_request_not_paid_body(body) {
		try {
			if (!body) return body;
			if (typeof URLSearchParams !== "undefined" && body instanceof URLSearchParams) {
				force_payment_request_not_paid_params(body);
				return body;
			}
			if (typeof FormData !== "undefined" && body instanceof FormData) {
				var filters = normalize_reportview_filters(body.get("filters"));
				if (body.get("doctype") === "Payment Request" && !has_payment_request_not_paid_filter(filters)) {
					filters.push(["Payment Request", "status", "!=", "Paid"]);
					body.set("filters", JSON.stringify(filters));
				}
				return body;
			}
			if (typeof body === "string") {
				var params = new URLSearchParams(body);
				if (force_payment_request_not_paid_params(params)) return params.toString();
			}
		} catch (e) {}
		return body;
	}

	function patch_payment_request_reportview_call() {
		if (!frappe || typeof frappe.call !== "function") return false;
		if (frappe.call._backdesk_payment_request_filter_patched) return true;

		var original_call = frappe.call;
		var reportview_methods = {
			"frappe.desk.reportview.get": true,
			"frappe.desk.reportview.get_count": true,
			"frappe.desk.reportview.get_list": true,
		};

		frappe.call = function (opts) {
			try {
				if (typeof opts === "object" && opts && reportview_methods[opts.method]) {
					force_payment_request_not_paid(opts.args);
				}
			} catch (e) {}
			return original_call.apply(this, arguments);
		};
		frappe.call._backdesk_payment_request_filter_patched = true;
		return true;
	}

	function try_patch_payment_request_reportview_call(n) {
		if (n <= 0) return;
		if (!patch_payment_request_reportview_call()) {
			setTimeout(function () { try_patch_payment_request_reportview_call(n - 1); }, 300);
		}
	}

	function patch_payment_request_reportview_transport() {
		try {
			if (window.XMLHttpRequest && !window.XMLHttpRequest.prototype._backdesk_payment_request_filter_patched) {
				var original_open = window.XMLHttpRequest.prototype.open;
				var original_send = window.XMLHttpRequest.prototype.send;
				window.XMLHttpRequest.prototype.open = function (method, url) {
					this._backdesk_reportview_url = reportview_url(url);
					return original_open.apply(this, arguments);
				};
				window.XMLHttpRequest.prototype.send = function (body) {
					if (this._backdesk_reportview_url) body = force_payment_request_not_paid_body(body);
					return original_send.call(this, body);
				};
				window.XMLHttpRequest.prototype._backdesk_payment_request_filter_patched = true;
			}

			if (window.fetch && !window.fetch._backdesk_payment_request_filter_patched) {
				var original_fetch = window.fetch;
				window.fetch = function (input, init) {
					try {
						var url = typeof input === "string" ? input : input && input.url;
						if (reportview_url(url) && init && init.body) {
							init = Object.assign({}, init, {
								body: force_payment_request_not_paid_body(init.body),
							});
						}
					} catch (e) {}
					return original_fetch.apply(this, arguments);
				};
				window.fetch._backdesk_payment_request_filter_patched = true;
			}
			return true;
		} catch (e) {
			return false;
		}
	}

	function inject_workspace_fullbleed_styles() {
		if (document.getElementById("backdesk-workspace-fullbleed-js")) return;
		var style = document.createElement("style");
		style.id = "backdesk-workspace-fullbleed-js";
		style.textContent = [
			"body.backdesk-workspace-fullbleed { --page-max-width: none; --content-width: 100%; --backdesk-workspace-content-padding: clamp(16px, 1.5vw, 24px); }",
			"body.backdesk-workspace-fullbleed .main-section,",
			"body.backdesk-workspace-fullbleed .page-container,",
			"body.backdesk-workspace-fullbleed .page-wrapper,",
			"body.backdesk-workspace-fullbleed .page-content,",
			"body.backdesk-workspace-fullbleed .page-body,",
			"body.backdesk-workspace-fullbleed .container.page-body,",
			"body.backdesk-workspace-fullbleed .layout-main,",
			"body.backdesk-workspace-fullbleed .layout-main-section-wrapper,",
			"body.backdesk-workspace-fullbleed .layout-main-section,",
			"body.backdesk-workspace-fullbleed .layout-main-section > .container,",
			"body.backdesk-workspace-fullbleed .layout-main-section > .container-fluid {",
			"  max-width: none !important;",
			"  width: 100% !important;",
			"}",
			"body.backdesk-workspace-fullbleed .page-body,",
			"body.backdesk-workspace-fullbleed .container.page-body {",
			"  box-sizing: border-box !important;",
			"  padding-left: var(--backdesk-workspace-content-padding, 20px) !important;",
			"  padding-right: var(--backdesk-workspace-content-padding, 20px) !important;",
			"}",
		].join("\n");
		document.head.appendChild(style);
	}

	function set_workspace_fullbleed_class(reason) {
		try {
			var route = frappe.get_route ? frappe.get_route() : [];
			var is_workspace = !!workspace_slug_from_route(route);
			if (!is_workspace && !route.length) is_workspace = !!document.querySelector(".workspace-body");
			document.body.classList.toggle("backdesk-workspace-fullbleed", is_workspace);
			if (is_workspace) document.body.setAttribute("data-backdesk-workspace-fullbleed", reason || "1");
			else document.body.removeAttribute("data-backdesk-workspace-fullbleed");
		} catch (e) {}
	}

	function init() {
		var sb = document.querySelector(".body-sidebar-container");
		if (!sb) return false;
		if (_initialized) return true;
		_initialized = true;

		inject_workspace_fullbleed_styles();
		set_workspace_fullbleed_class("init");
		patch_payment_request_reportview_transport();
		try_patch_payment_request_reportview_call(20);
		try_patch_typelink_get_path(20);
		try_patch_workspace_switch(20);
		try_patch_workspace_save_page(20);
		try_watch_sidebar_title(20);
		$(window).on("beforeunload", save_last_workspace);

		[200, 600, 1500, 3000].forEach(function (ms) {
			setTimeout(save_last_workspace, ms);
			setTimeout(function () { set_workspace_fullbleed_class("init+" + ms); }, ms);
			setTimeout(enforce_correct_workspace, ms);
		});

		sb.addEventListener("click", on_click, true);

		var overriding = false;
		var observer = new MutationObserver(function () {
			if (!_last_clicked || overriding) return;
			var correct = find_dom_by_label(_last_clicked.label);
			if (!correct) return;
			var inner = correct.querySelector(".standard-sidebar-item") || correct;
			if (inner.classList.contains("active-sidebar")) return;
			overriding = true;
			set_active(correct);
			setTimeout(function () { overriding = false; }, 50);
		});
		observer.observe(sb, { attributes: true, attributeFilter: ["class"], subtree: true });

		var on_route = function () {
			set_workspace_fullbleed_class("route");
			setTimeout(function () { fix_active_retry(5); }, 300);
			setTimeout(enforce_correct_workspace, 200);
			setTimeout(enforce_correct_workspace, 600);
			setTimeout(function () { set_workspace_fullbleed_class("route-300"); }, 300);
			setTimeout(save_last_workspace, 300);
		};
		if (frappe.router && typeof frappe.router.on === "function") frappe.router.on("change", on_route);
		else $(document).on("page-change", on_route);

		setTimeout(function () { fix_active_retry(5); }, 300);
		return true;
	}

	function try_init(n) {
		if (n <= 0) return;
		if (!init()) setTimeout(function () { try_init(n - 1); }, 500);
	}

	$(document).ready(function () { try_init(10); });
})();

// mathAgents explorer. Reads api.json and library.json (written by scripts/build_api_site.py) and renders them.
// Security: every value is inserted as text (textContent / createTextNode), never as HTML; links are allowed only
// to this site (relative paths) or to https://github.com/. tests/test_api_site.py checks this file for HTML sinks.
"use strict";

const state = { api: null, library: null, apiIndex: [] };

// --- DOM helpers -------------------------------------------------------------------------------------------------

function el(tag, props, ...children) {
  const node = document.createElement(tag);
  if (props) {
    for (const [key, value] of Object.entries(props)) {
      if (value === null || value === undefined || value === false) continue;
      if (key === "className") node.className = value;
      else if (key === "text") node.textContent = String(value);
      else if (key === "href") {
        const safe = safeHref(value);
        if (safe) node.setAttribute("href", safe);
      } else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, String(value));
    }
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

function safeHref(value) {
  // Resolve the way the browser will, then allow only this site's origin or https://github.com.
  let url;
  try {
    url = new URL(String(value), location.href);
  } catch (e) {
    return null;
  }
  if (url.origin === location.origin || url.origin === "https://github.com") return url.href;
  return null;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function code(text) {
  return el("code", { text });
}

function external(href, text) {
  return el("a", { href, rel: "noopener noreferrer", target: "_blank" }, text);
}

// --- tabs --------------------------------------------------------------------------------------------------------

const VIEWS = ["api", "library", "pipeline"];

function showView(name, push) {
  if (!VIEWS.includes(name)) name = "api";
  for (const v of VIEWS) {
    const tab = document.getElementById(`tab-${v}`);
    const panel = document.getElementById(`view-${v}`);
    const on = v === name;
    tab.setAttribute("aria-selected", on ? "true" : "false");
    tab.tabIndex = on ? 0 : -1;
    panel.hidden = !on;
  }
  if (push) history.replaceState(null, "", `#${name}`);
}

function wireTabs() {
  VIEWS.forEach((v, i) => {
    const tab = document.getElementById(`tab-${v}`);
    tab.addEventListener("click", () => showView(v, true));
    tab.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      const next = VIEWS[(i + (e.key === "ArrowRight" ? 1 : VIEWS.length - 1)) % VIEWS.length];
      showView(next, true);
      document.getElementById(`tab-${next}`).focus();
    });
  });
  showView((location.hash || "#api").slice(1).split("/")[0], false);
}

// --- API view ----------------------------------------------------------------------------------------------------

function buildApiIndex(api) {
  const rows = [];
  for (const mod of api.modules) {
    for (const n of mod.names) {
      rows.push({ mod, n, hay: `${mod.module}.${n.name} ${n.signature} ${n.summary}`.toLowerCase() });
    }
  }
  return rows;
}

function renderApiFilters() {
  const modSel = document.getElementById("api-module");
  const kindSel = document.getElementById("api-kind");
  for (const mod of state.api.modules) modSel.appendChild(el("option", { value: mod.module, text: mod.module }));
  const kinds = [...new Set(state.apiIndex.map((r) => r.n.kind))].sort();
  for (const k of kinds) kindSel.appendChild(el("option", { value: k, text: k }));
  for (const id of ["api-query", "api-module", "api-kind"]) {
    document.getElementById(id).addEventListener("input", renderApiList);
  }
}

function renderApiList() {
  const q = document.getElementById("api-query").value.trim().toLowerCase();
  const mod = document.getElementById("api-module").value;
  const kind = document.getElementById("api-kind").value;
  const words = q.split(/\s+/).filter(Boolean);
  const hits = state.apiIndex.filter(
    (r) => (!mod || r.mod.module === mod) && (!kind || r.n.kind === kind) && words.every((w) => r.hay.includes(w)),
  );
  const list = document.getElementById("api-list");
  clear(list);
  for (const r of hits) {
    const id = `${r.mod.module}.${r.n.name}`;
    const button = el(
      "button",
      { type: "button", className: "item", "data-id": id, onclick: () => selectApi(r, button) },
      el("span", { className: "name", text: r.n.name }),
      el("span", { className: `kind kind-${r.n.kind}`, text: r.n.kind }),
      el("span", { className: "mod", text: r.mod.module }),
    );
    list.appendChild(el("li", null, button));
  }
  document.getElementById("api-count").textContent =
    `${hits.length} of ${state.apiIndex.length} public names in ${state.api.modules.length} modules ` +
    `(mathagents ${state.api.version})`;
}

function selectApi(r, button) {
  for (const b of document.querySelectorAll("#api-list .item[aria-current]")) b.removeAttribute("aria-current");
  if (button) button.setAttribute("aria-current", "true");
  const d = document.getElementById("api-detail");
  clear(d);
  d.appendChild(el("p", { className: "eyebrow" }, `${r.mod.module} · ${r.n.kind}`));
  d.appendChild(el("h2", { text: r.n.name }));
  d.appendChild(el("pre", { className: "sig" }, code(r.n.signature)));
  d.appendChild(el("p", { text: r.n.summary || "No summary in the source; see the reference page." }));
  if (r.n.fields && r.n.fields.length) {
    d.appendChild(el("h3", { text: "Fields" }));
    d.appendChild(el("ul", { className: "mono" }, r.n.fields.map((f) => el("li", null, code(f)))));
  }
  if (r.n.methods && r.n.methods.length) {
    d.appendChild(el("h3", { text: "Methods" }));
    d.appendChild(el("ul", { className: "mono" }, r.n.methods.map((m) => el("li", null, code(m)))));
  }
  d.appendChild(
    el(
      "p",
      { className: "links" },
      el("a", { href: `../${r.mod.page}` }, "Reference page"),
      " · ",
      external(r.n.source, "Source on GitHub"),
    ),
  );
  if (r.mod.summary) d.appendChild(el("p", { className: "muted" }, `Module: ${r.mod.summary}`));
}

// --- Proof library view ------------------------------------------------------------------------------------------

function renderLibrary() {
  const lib = state.library;
  const pins = document.getElementById("library-pins");
  pins.appendChild(el("span", null, "Lean pin ", code(lib.pins.lean_toolchain)));
  pins.appendChild(el("span", null, "Mathlib ", code(lib.pins.mathlib_rev.slice(0, 12))));
  if (lib.built_from && lib.built_from.commit) {
    pins.appendChild(el("span", null, "Data built from commit ", code(lib.built_from.commit.slice(0, 7)), ` at ${lib.built_from.built_at}`));
  }
  const root = document.getElementById("library-list");
  for (const d of lib.dossiers) root.appendChild(renderDossier(d));
}

function resultLine(d) {
  if (!d.result_status.length) {
    return el("p", { className: "result result-none" }, "No ", code("Result status:"), " line yet, so the result is open.");
  }
  return el(
    "div",
    { className: "result" },
    el("p", null, d.result_status.map((r) => el("span", null, code(`Result status: ${r.value}`), ` (from ${r.file})`))),
    el(
      "p",
      { className: "caveat" },
      "This is the Lean half of the standard only: the project accepts a result as Blueprint + Lean, and this dossier has no blueprint yet.",
    ),
  );
}

function stageStrip(d) {
  const present = new Set(d.stages_with_artifacts);
  const label = (s) => (s.artifacts.length === 0 ? "lists no files" : present.has(s.number) ? "files present" : "files absent");
  return el(
    "div",
    { className: "stage-wrap" },
    el(
      "ol",
      { className: "stages", "aria-label": "Pipeline stages and whether their files are present" },
      state.library.stages.map((s) =>
        el(
          "li",
          { className: s.artifacts.length === 0 ? "na" : present.has(s.number) ? "on" : "", title: `Stage ${s.number}, ${s.name}: ${label(s)}` },
          el("span", { className: "num", text: String(s.number) }),
          el("span", { className: "visually-hidden", text: `: ${label(s)}` }),
        ),
      ),
    ),
    el(
      "p",
      { className: "muted small" },
      "A filled circle means the files the pipeline lists for that stage are present. It does not mean the stage's gate passed. Stages 5 and 6 list no files of their own.",
    ),
  );
}

function renderDossier(d) {
  const card = (d.card && d.card.fields) || {};
  const continued = new Set((d.card && d.card.continued) || []);
  const stale = d.snapshot && d.snapshot.sources_current !== true;
  const snapshot = d.snapshot
    ? el(
        "div",
        null,
        el(
          "p",
          { className: "muted" },
          "Kernel snapshot: commit ",
          code(d.snapshot.commit.slice(0, 7)),
          `, checked ${d.snapshot.checked_at}`,
          d.snapshot.dirty ? " (dirty tree)" : ", clean tree",
          d.snapshot.lean_version ? [", under ", code(d.snapshot.lean_version.replace(/^Lean \(version ([^,]+),.*$/, "Lean $1"))] : null,
          ".",
        ),
        stale
          ? el(
              "p",
              { className: "caveat" },
              d.snapshot.sources_current === false
                ? "The Lean sources have changed since this snapshot (their G-KERNEL source hash differs), so these statuses describe the sources at that commit, not necessarily today's. A fresh G-KERNEL run gives the current status."
                : "Whether the Lean sources have changed since this snapshot could not be determined.",
            )
          : null,
      )
    : el("p", { className: "muted" }, "No kernel snapshot yet. A snapshot is taken at Stage 8.");
  const decls = d.declarations.length
    ? el(
        "div",
        { className: "table-wrap" },
        el(
          "table",
          { className: "decls" },
          el("thead", null, el("tr", null, ["Declaration", "Kernel status (snapshot)", "Axioms", "G-FID"].map((h) => el("th", { text: h })))),
          el("tbody", null, d.declarations.map((row) => declRow(row, d, stale))),
        ),
      )
    : el("p", { className: "muted", text: "No declarations recorded yet." });
  return el(
    "details",
    { className: "dossier", open: d.result_status.length ? null : "" },
    el(
      "summary",
      null,
      d.pilot ? el("span", { className: "pilot", text: `Pilot ${d.pilot}` }) : null,
      el("span", { className: "title", text: d.title }),
      el("span", { className: "slug", text: d.slug }),
    ),
    el(
      "div",
      { className: "body" },
      resultLine(d),
      stageStrip(d),
      el(
        "dl",
        { className: "card" },
        ["Informal statement", "Source", "Domain", "Object logic", "Engine", "Reading"].flatMap((k) =>
          card[k]
            ? [
                el("dt", { text: k }),
                el("dd", null, card[k], continued.has(k) ? [" … ", external(d.problem_card, "(continues in the problem card)")] : null),
              ]
            : [],
        ),
      ),
      d.readings.length
        ? el("div", null, el("h3", { text: "Readings" }), el("ul", null, d.readings.map((r) => el("li", null, code(r.id), ` ${r.title}`))))
        : null,
      el("h3", { text: "Declarations" }),
      snapshot,
      decls,
      el("p", { className: "links" }, external(d.files, "Dossier files on GitHub")),
    ),
  );
}

function declRow(row, d, stale) {
  const short = d.lean_namespace && row.name.startsWith(`${d.lean_namespace}.`)
    ? row.name.slice(d.lean_namespace.length + 1)
    : row.name;
  // G-KERNEL reports a definition or structure as "proved" when it elaborated with no open marker; say "checked".
  const isTheorem = row.kind === "theorem";
  let status;
  if (!row.snapshot_status) {
    status = el("span", { className: "status status-none", text: "no kernel snapshot yet" });
  } else {
    const word = row.snapshot_status === "proved" && !isTheorem ? "checked" : row.snapshot_status;
    status = el("span", { className: `status ${stale ? "status-stale" : `status-${row.snapshot_status}`}`, text: word });
  }
  let gfid = el("span", { className: "muted", text: "—" });
  if (row.gfid) {
    const note = {
      matches: null,
      differs: el("span", { className: "warn", text: " (its fingerprint differs from the snapshot's)" }),
      unchecked: el("span", { className: "muted", text: " (fingerprint not yet checked against a kernel snapshot)" }),
    }[row.gfid.check];
    gfid = el("span", { title: `statement fingerprint ${row.gfid.statement_fingerprint}` }, `${row.gfid.status}, ${row.gfid.date}`, note);
  }
  return el(
    "tr",
    null,
    el("td", null, row.source ? external(row.source, short) : short, row.kind ? el("span", { className: "kind", text: ` ${row.kind}` }) : null),
    el("td", null, status),
    el("td", { className: "mono small", text: row.axioms ? row.axioms.join(", ") || "none" : "—" }),
    el("td", null, gfid),
  );
}

// --- Pipeline view -----------------------------------------------------------------------------------------------

function table(id, headers, rows) {
  const t = document.getElementById(id);
  t.appendChild(el("thead", null, el("tr", null, headers.map((h) => el("th", { text: h })))));
  t.appendChild(el("tbody", null, rows.map((r) => el("tr", null, r.map((c) => el("td", null, c))))));
}

function renderPipeline() {
  const lib = state.library;
  table(
    "stages-table",
    ["Stage", "Name", "Agents", "Artifacts"],
    lib.stages.map((s) => [String(s.number), s.name, s.agents.map((a) => `@${a}`).join(", "), s.artifacts.join(", ") || "—"]),
  );
  const gates = document.getElementById("gates-list");
  for (const g of lib.gates) gates.appendChild(el("li", null, code(g)));
  table(
    "logics-table",
    ["Id", "Name", "Family", "Embedding", "Status"],
    lib.object_logics.map((l) => [code(l.id), l.name || "", l.family || "", l.embedding || "", l.status || ""]),
  );
  table(
    "engines-table",
    ["Id", "Name", "Kind", "Result trust", "Evidence"],
    lib.prover_engines.map((e) => [code(e.id), e.name || "", e.kind || "", e.result_trust || "", e.evidence_status || ""]),
  );
  const ax = document.getElementById("axioms");
  ax.appendChild(el("p", null, "Base axioms: ", lib.axioms.base.map((a, i) => [i ? ", " : "", code(a)])));
  ax.appendChild(
    el("p", null, "Approved additional axioms: ", lib.axioms.approved.length ? lib.axioms.approved.map((a, i) => [i ? ", " : "", code(String(a.name || a))]) : "none"),
  );
}

// --- boot --------------------------------------------------------------------------------------------------------

async function load(name) {
  const res = await fetch(name, { credentials: "same-origin" });
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
}

async function boot() {
  wireTabs();
  const status = document.getElementById("load-status");
  try {
    [state.api, state.library] = await Promise.all([load("api.json"), load("library.json")]);
  } catch (err) {
    status.textContent = `Could not load the explorer data (${err.message}). The data files are generated when the site is built.`;
    status.classList.add("error");
    return;
  }
  status.hidden = true;
  state.apiIndex = buildApiIndex(state.api);
  renderApiFilters();
  renderApiList();
  renderLibrary();
  renderPipeline();
}

boot();

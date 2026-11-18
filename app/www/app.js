/* SellPilot dashboard. Reads sales straight from Polar, starts the bot and edits its settings through GitHub. */
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const KINDS = {
  "annual-planner": "Yearly planner", "wall-calendar": "Calendar", "budget-planner": "Budget planner", "meal-planner": "Meal planner",
  "fitness-planner": "Fitness planner", "self-care-journal": "Self-care journal", "reading-journal": "Reading journal",
  "cleaning-planner": "Cleaning planner", "student-planner": "Student planner", "teacher-planner": "Teacher planner",
  "small-business-planner": "Small business", "wedding-planner": "Wedding planner", "baby-log": "Baby log",
  "pet-planner": "Pet planner", "travel-planner": "Travel planner", "christmas-planner": "Christmas planner",
  "new-year-planner": "New Year planner",
};

const S = {
  get(k, d = "") { try { return localStorage.getItem("sp_" + k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem("sp_" + k, v); } catch {} },
};
const state = { products: null, orders: null, runs: null, cfg: null, cfgSha: null, err: "" };

// ---------------------------------------------------------------- APIs
async function polar(path, params = {}) {
  const base = S.get("server", "production") === "sandbox" ? "https://sandbox-api.polar.sh" : "https://api.polar.sh";
  const q = new URLSearchParams(params).toString();
  const r = await fetch(`${base}${path}${q ? "?" + q : ""}`, { headers: { Authorization: "Bearer " + S.get("polar"), Accept: "application/json" } });
  if (!r.ok) throw new Error(`Polar ${r.status}: ${(await r.text()).slice(0, 160)}`);
  return r.json();
}
async function polarAll(path, params = {}) {
  let page = 1, out = [];
  for (;;) {
    const res = await polar(path, { ...params, page, limit: 100 });
    out = out.concat(res.items || []);
    if (page >= ((res.pagination || {}).max_page || 1) || page > 50) return out;
    page++;
  }
}
async function polarPatch(id, body) {
  const base = S.get("server", "production") === "sandbox" ? "https://sandbox-api.polar.sh" : "https://api.polar.sh";
  const r = await fetch(`${base}/v1/products/${id}`, { method: "PATCH", headers: { Authorization: "Bearer " + S.get("polar"), "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`Polar ${r.status}`);
  return r.json();
}
async function gh(path, opts = {}) {
  const r = await fetch(`https://api.github.com/repos/${S.get("repo")}${path}`, {
    ...opts, headers: { Authorization: "Bearer " + S.get("gh"), Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", ...(opts.headers || {}) },
  });
  if (!r.ok && r.status !== 204) throw new Error(`GitHub ${r.status}: ${(await r.text()).slice(0, 160)}`);
  return r.status === 204 ? {} : r.json();
}
const b64d = (s) => decodeURIComponent(escape(atob(s.replace(/\n/g, ""))));
const b64e = (s) => btoa(unescape(encodeURIComponent(s)));

// ---------------------------------------------------------------- data
const PAID = new Set(["paid", "partially_refunded"]);
const earned = (o) => (o.net_amount || 0) - (o.platform_fee_amount || 0) - (o.refunded_amount || 0);
function money(c, cur) {
  cur = (cur || (state.cfg && state.cfg.currency) || "usd").toUpperCase();
  try { return new Intl.NumberFormat(undefined, { style: "currency", currency: cur }).format((c || 0) / 100); } catch { return ((c || 0) / 100).toFixed(2) + " " + cur; }
}
function price(p) { const pr = (p.prices || []).find((x) => x.amount_type === "fixed" && !x.is_archived); return pr ? pr.price_amount : 0; }
function totals() {
  const now = new Date(), day = 864e5, today = now.toISOString().slice(0, 10);
  const t = { all: 0, n: 0, d30: 0, n30: 0, today: 0, ntoday: 0, cur: null, days: {}, byProduct: {} };
  for (const o of state.orders || []) {
    if (!PAID.has(o.status)) continue;
    const e = earned(o), d = (o.created_at || "").slice(0, 10);
    t.cur = t.cur || o.currency; t.all += e; t.n++;
    if (now - new Date(o.created_at) < 30 * day) { t.d30 += e; t.n30++; t.days[d] = (t.days[d] || 0) + e; }
    if (d === today) { t.today += e; t.ntoday++; }
    const bp = (t.byProduct[o.product_id] ||= { n: 0, e: 0 }); bp.n++; bp.e += e;
  }
  return t;
}

async function load(force) {
  if (!S.get("polar")) return;
  setStatus("syncing…");
  try {
    if (force || !state.products) {
      const [a, b] = await Promise.all([polarAll("/v1/products/", { is_archived: "false" }), polarAll("/v1/products/", { is_archived: "true" })]);
      state.products = a.concat(b).filter((p) => (p.metadata || {}).sp);
    }
    if (force || !state.orders) state.orders = await polarAll("/v1/orders/", { sorting: "-created_at" });
    state.err = "";
    S.set("cache", JSON.stringify({ products: state.products, orders: state.orders, at: Date.now() }));
  } catch (e) { state.err = e.message; }
  if (S.get("gh") && S.get("repo")) {
    try { state.runs = (await gh("/actions/workflows/bot.yml/runs?per_page=5")).workflow_runs || []; } catch (e) { state.runs = null; }
  }
  setStatus(state.err ? "offline" : "updated " + new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
}
function setStatus(s) { $("#status").textContent = s; }

// ---------------------------------------------------------------- views
const views = {
  home() {
    if (!S.get("polar")) return `<div class="card"><h2>Welcome</h2><p>SellPilot makes printable products, sells them through Polar (they handle payment, VAT and delivery) and promotes them for you.</p><p class="sub">Connect your Polar token in Settings to see your earnings.</p><button class="btn" onclick="go('settings')">Open settings</button></div>`;
    const t = totals(), cur = t.cur;
    const days = [...Array(30)].map((_, i) => { const d = new Date(Date.now() - (29 - i) * 864e5).toISOString().slice(0, 10); return t.days[d] || 0; });
    const mx = Math.max(1, ...days);
    const live = (state.products || []).filter((p) => !p.is_archived);
    const best = Object.entries(t.byProduct).sort((a, b) => b[1].e - a[1].e).slice(0, 5)
      .map(([id, v]) => { const p = (state.products || []).find((x) => x.id === id); return p ? row(p, `${v.n} sold · ${money(v.e, cur)}`) : ""; }).join("");
    const run = (state.runs || [])[0];
    const runTxt = run ? `${run.status === "completed" ? (run.conclusion === "success" ? '<span class="ok">✓ last run OK</span>' : '<span class="err">✗ last run failed</span>') : "⏳ running now"} · ${new Date(run.created_at).toLocaleString()}` : "";
    return `${state.err ? `<div class="card err">${esc(state.err)}</div>` : ""}
    <div class="card"><h2>Earned (after fees)</h2><div class="big">${money(t.d30, cur)}</div><div class="sub">last 30 days · ${t.n30} sales</div>
      <div class="chart">${days.map((v) => `<div style="height:${(v / mx) * 100}%"></div>`).join("")}</div>
      <div class="kpis" style="margin-top:12px"><div class="kpi"><b>${money(t.today, cur)}</b><span>today (${t.ntoday})</span></div>
      <div class="kpi"><b>${money(t.all, cur)}</b><span>all time (${t.n})</span></div><div class="kpi"><b>${live.length}</b><span>products for sale</span></div></div></div>
    <div class="card"><h2>Bot</h2><div class="sub">${runTxt || "Runs every day automatically."}</div>
      <button class="btn" id="runbtn" onclick="runBot()" ${S.get("gh") ? "" : "disabled"}>Run the bot now</button>
      ${S.get("site") ? `<button class="btn alt" onclick="openUrl('${esc(S.get("site"))}')">Open my shop website</button>` : ""}
      ${S.get("gh") ? "" : '<p class="muted">Add a GitHub token in Settings to start runs from here.</p>'}</div>
    <div class="card"><h2>Best sellers</h2>${best || '<p class="muted">No sales yet. New products go live every day; the first sales usually take a few weeks while search engines and Pinterest pick them up.</p>'}</div>`;
  },
  products() {
    const t = totals();
    const ps = (state.products || []).slice().sort((a, b) => (a.is_archived - b.is_archived) || (b.created_at || "").localeCompare(a.created_at || ""));
    return `<div class="card"><h2>${ps.filter((p) => !p.is_archived).length} for sale · ${ps.filter((p) => p.is_archived).length} archived</h2>
      ${ps.map((p) => { const s = t.byProduct[p.id]; return row(p, `${money(price(p))} · ${s ? s.n + " sold" : "no sales yet"}`, true); }).join("") || '<p class="muted">The bot has not published anything yet.</p>'}</div>`;
  },
  sales() {
    const os = (state.orders || []).slice(0, 100);
    return `<div class="card"><h2>Recent sales</h2>${os.map((o) => `<div class="row"><div class="t"><b>${esc((o.product || {}).name || o.description || "Order")}</b>
      <span>${new Date(o.created_at).toLocaleString()} · ${esc(o.billing_address ? o.billing_address.country : "")} ${o.status !== "paid" ? `<span class="pill bad">${esc(o.status)}</span>` : ""}</span></div>
      <div class="v">${money(earned(o), o.currency)}</div></div>`).join("") || '<p class="muted">No sales yet.</p>'}</div>`;
  },
  settings() {
    const c = state.cfg;
    return `<div class="card"><h2>Connections</h2>
      <label>Polar access token (Polar › Settings › Developers › New token)</label><input id="s_polar" type="password" value="${esc(S.get("polar"))}" placeholder="polar_oat_…">
      <label>Polar server</label><select id="s_server"><option value="production">Live (real money)</option><option value="sandbox" ${S.get("server") === "sandbox" ? "selected" : ""}>Sandbox (test)</option></select>
      <label>GitHub repository</label><input id="s_repo" value="${esc(S.get("repo"))}" placeholder="KingAtdhe/sellpilot">
      <label>GitHub token (fine-grained: this repo, Contents + Actions read/write)</label><input id="s_gh" type="password" value="${esc(S.get("gh"))}" placeholder="github_pat_…">
      <label>Shop website address</label><input id="s_site" value="${esc(S.get("site"))}" placeholder="https://kingatdhe.github.io/sellpilot/">
      <button class="btn" onclick="saveConn()">Save and connect</button><p id="connmsg" class="muted"></p></div>
    <div class="card"><h2>Bot settings</h2>${c ? botSettings(c) : `<p class="muted">${S.get("gh") ? "Loading…" : "Connect GitHub above to change what the bot does."}</p>`}</div>`;
  },
};

function botSettings(c) {
  const sw = (k, label) => `<div class="switch">${label}<input type="checkbox" id="c_${k}" ${c[k] ? "checked" : ""}></div>`;
  const only = new Set(c.only_kinds || []);
  return `${sw("paused", "Pause the bot")}
    <label>Shop name</label><input id="c_store_name" value="${esc(c.store_name)}">
    <label>New products per day</label><input id="c_products_per_run" type="number" min="0" max="10" value="${c.products_per_run}">
    <label>Most products for sale at once</label><input id="c_max_products" type="number" min="1" value="${c.max_products}">
    <label>Price level (1 = normal, 1.2 = 20% higher)</label><input id="c_price_multiplier" type="number" step="0.05" value="${c.price_multiplier}">
    <label>Currency (for new products)</label><select id="c_currency">${["usd", "eur", "gbp"].map((x) => `<option ${c.currency === x ? "selected" : ""}>${x}</option>`).join("")}</select>
    <label>Pinterest pins per day</label><input id="c_pins_per_run" type="number" min="0" max="25" value="${c.pins_per_run}">
    ${sw("price_tests", "Automatic price tests")}${sw("bundles", "Make discount bundles")}${sw("campaigns", "Seasonal sales (Black Friday, New Year…)")}
    <label>Only make these (none ticked = the bot picks by demand)</label>
    <div class="kinds">${Object.entries(KINDS).map(([k, v]) => `<label><input type="checkbox" class="kind" value="${k}" ${only.has(k) ? "checked" : ""}>${v}</label>`).join("")}</div>
    <button class="btn" onclick="saveCfg()">Save bot settings</button><p id="cfgmsg" class="muted"></p>`;
}

function row(p, info, actions) {
  const img = ((p.medias || [])[0] || {}).public_url || "";
  const md = p.metadata || {};
  const pills = (md.sp_bundle ? '<span class="pill good">bundle</span>' : "") + (p.is_archived ? '<span class="pill">archived</span>' : "");
  const site = S.get("site");
  const url = site && md.sp_slug ? `${site.replace(/\/$/, "")}/p/${md.sp_slug}.html` : md.sp_link;
  return `<div class="row"><img src="${esc(img)}" alt="" loading="lazy" onclick="openUrl('${esc(url || "")}')"><div class="t" onclick="openUrl('${esc(url || "")}')"><b>${esc(p.name.split(" | ")[0])}</b><span>${pills}${esc(info)}</span></div>
    ${actions ? `<button class="pill" onclick="toggleArchive('${p.id}',${!p.is_archived})">${p.is_archived ? "Sell again" : "Stop selling"}</button>` : ""}</div>`;
}

// ---------------------------------------------------------------- actions
let tab = "home";
async function go(t) {
  tab = t;
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === t));
  render();
  if (t === "settings" && S.get("gh") && !state.cfg) { await loadCfg(); render(); }
}
function render() { $("#view").innerHTML = views[tab](); }
window.go = go;
window.openUrl = (u) => { if (u) window.open(u, "_blank"); };
window.saveConn = async () => {
  for (const k of ["polar", "server", "repo", "gh", "site"]) S.set(k, $("#s_" + k).value.trim());
  $("#connmsg").textContent = "Connecting…";
  state.products = state.orders = state.cfg = null;
  await load(true);
  if (S.get("gh")) await loadCfg();
  $("#connmsg") && ($("#connmsg").innerHTML = state.err ? `<span class="err">${esc(state.err)}</span>` : '<span class="ok">Connected.</span>');
  render();
};
async function loadCfg() {
  try {
    const f = await gh("/contents/bot/config.json");
    state.cfg = JSON.parse(b64d(f.content)); state.cfgSha = f.sha;
  } catch (e) { state.cfg = null; setStatus("settings: " + e.message.slice(0, 40)); }
}
window.saveCfg = async () => {
  const c = { ...state.cfg };
  for (const k of ["paused", "price_tests", "bundles", "campaigns"]) c[k] = $("#c_" + k).checked;
  c.store_name = $("#c_store_name").value.trim() || c.store_name;
  for (const k of ["products_per_run", "max_products", "pins_per_run"]) c[k] = parseInt($("#c_" + k).value, 10) || 0;
  c.price_multiplier = parseFloat($("#c_price_multiplier").value) || 1;
  c.currency = $("#c_currency").value;
  c.only_kinds = [...document.querySelectorAll(".kind:checked")].map((x) => x.value);
  $("#cfgmsg").textContent = "Saving…";
  try {
    const r = await gh("/contents/bot/config.json", { method: "PUT", body: JSON.stringify({ message: "Settings changed in the SellPilot app", content: b64e(JSON.stringify(c, null, 2) + "\n"), sha: state.cfgSha }) });
    state.cfg = c; state.cfgSha = r.content.sha;
    $("#cfgmsg").innerHTML = '<span class="ok">Saved. The next run uses these settings.</span>';
  } catch (e) { $("#cfgmsg").innerHTML = `<span class="err">${esc(e.message)}</span>`; }
};
window.runBot = async () => {
  const b = $("#runbtn"); b.disabled = true; b.textContent = "Starting…";
  try {
    await gh("/actions/workflows/bot.yml/dispatches", { method: "POST", body: JSON.stringify({ ref: "main" }) });
    b.textContent = "Started - new products appear in a few minutes";
    setTimeout(() => load(true).then(render), 15000);
  } catch (e) { b.textContent = "Could not start: " + e.message.slice(0, 60); b.disabled = false; }
};
window.toggleArchive = async (id, archive) => {
  try { await polarPatch(id, { is_archived: archive }); const p = state.products.find((x) => x.id === id); p.is_archived = archive; render(); }
  catch (e) { alert(e.message); }
};

document.querySelectorAll(".tabs button").forEach((b) => (b.onclick = () => go(b.dataset.tab)));
try { const c = JSON.parse(S.get("cache", "null")); if (c) { state.products = c.products; state.orders = c.orders; } } catch {}
render();
load(true).then(render);
setInterval(() => load(true).then(() => tab !== "settings" && render()), 5 * 60 * 1000);

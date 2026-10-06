const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const $ = (id) => document.getElementById(id);

const app = $("app");
const home = $("home");
const homeForm = $("homeForm");
const homeInput = $("homeInput");
const composer = $("composer");
const composerForm = $("composerForm");
const composerInput = $("composerInput");
const reader = $("reader");
const readingTitle = $("readingTitle");
const readingBody = $("readingBody");
const readingSections = $("readingSections");
const readingMeta = $("readingMeta");
const trailEl = $("trail");
const sideList = $("sideList");
const actionCount = $("actionCount");
const actionsEmpty = $("actionsEmpty");
const statusMeta = $("statusMeta");
const statusBranches = $("statusBranches");
const toolbar = $("toolbar");
const toolbarPreview = $("toolbarPreview");
const toolbarResults = $("toolbarResults");
const lensOverlay = $("lensOverlay");
const lensQuestion = $("lensQuestion");
const lensChip = $("lensChip");
const lensChipText = $("lensChipText");
const themeBtn = $("themeBtn");
const notesBtn = $("notesBtn");
const noteCount = $("noteCount");
const notebook = $("notebook");
const notesClose = $("notesClose");
const notesEmpty = $("notesEmpty");
const noteList = $("noteList");
const notesExport = $("notesExport");
const toastEl = $("toast");

const KIND_LOC = { dive: "↓", eli5: "→", example: "→", define: "→", note: "★" };
const KIND_ORDER = ["dive", "eli5", "example", "define", "note"];

const state = {
  lens: { familiarity: "basics", depth: "solid", style: "plain", goal: "curious" },
  question: "",
  nodes: new Map(),
  rootId: null,
  order: [],
  activeId: null,
  counter: 0,
  toolbarContext: null,
  marks: [],
  notes: [],
};

function escapeHtml(value) {
  return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/"/g, "&quot;");
}

function normalize(text) {
  return String(text).toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, " ").trim();
}

function truncate(text, n) {
  return text.length > n ? text.slice(0, n - 1).trim() + "…" : text;
}

function renderBody(raw) {
  return escapeHtml(raw).replace(
    /\*\*(.+?)\*\*/g,
    (m, t) => `<span class="anchor" data-term="${escapeAttr(t)}">${t}</span>`
  );
}

function streamInto(el, raw, done) {
  if (reduce) {
    el.innerHTML = renderBody(raw);
    if (done) done();
    return;
  }
  const words = raw.split(" ");
  let i = 0;
  el.classList.add("streaming");
  el.textContent = "";
  const step = () => {
    i = Math.min(words.length, i + 2);
    el.textContent = words.slice(0, i).join(" ");
    if (i < words.length) {
      setTimeout(step, 16);
    } else {
      el.classList.remove("streaming");
      el.innerHTML = renderBody(raw);
      if (done) done();
    }
  };
  setTimeout(step, 40);
}

function toast(message) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toastEl.classList.remove("show"), 2400);
}

function formatLens() {
  const l = state.lens;
  const fam = { new: "New", basics: "Basics", expert: "Expert" }[l.familiarity];
  const depth = { quick: "Quick", solid: "Solid", deep: "Deep" }[l.depth];
  const style = { plain: "Plain", analogy: "Analogies", technical: "Technical" }[l.style];
  return `${fam} · ${depth} · ${style}`;
}

function containerEl(id) {
  if (id === "root") return readingBody;
  const node = state.nodes.get(id);
  return node ? node.bodyEl : null;
}

function diveHost(parent) {
  let n = parent;
  while (n) {
    if (n.sectionsEl) return n.sectionsEl;
    n = n.parentId ? state.nodes.get(n.parentId) : null;
  }
  return readingSections;
}

function bloomAt(rect) {
  if (reduce || !rect) return;
  const pulse = document.createElement("span");
  pulse.className = "bloom-pulse";
  pulse.style.left = rect.left + rect.width / 2 + "px";
  pulse.style.top = rect.top + rect.height / 2 + "px";
  document.body.appendChild(pulse);
  pulse.addEventListener("animationend", () => pulse.remove());
}

function anchorRect(containerId, anchor) {
  const el = containerEl(containerId);
  if (!el) return null;
  const key = normalize(anchor);
  const span = Array.from(el.querySelectorAll(".anchor")).find((s) => normalize(s.dataset.term) === key);
  return span ? span.getBoundingClientRect() : null;
}

function createSection(containerId, anchor, kind) {
  const parent = state.nodes.get(containerId);
  if (!parent) return null;
  const clean = anchor.replace(/\s+/g, " ").trim();
  if (!clean) return null;

  const depth = parent.depth + 1;
  const data = generateNode(parent, clean, kind, state.lens);
  const id = "a" + ++state.counter;
  const node = {
    id,
    parentId: containerId,
    depth,
    kind,
    anchor: clean,
    title: data.title,
    body: data.body,
    citations: data.citations,
    estReadSeconds: data.estReadSeconds,
    collapsed: false,
  };
  state.nodes.set(id, node);

  const isDive = kind === "dive";
  const el = document.createElement(isDive ? "section" : "li");
  el.className = isDive ? "action-section kind-dive" : `side-card kind-${kind}`;
  el.dataset.id = id;
  el.dataset.depth = String(depth);
  el.innerHTML = `
    <header class="as-head">
      <button type="button" class="as-toggle" aria-expanded="true" aria-label="Collapse">▼</button>
      <span class="as-kind">${escapeHtml(KIND_LABELS[kind] || kind)}</span>
      <button type="button" class="as-anchor">“${escapeHtml(clean)}”</button>
      <button type="button" class="as-remove" aria-label="Remove section">✕</button>
    </header>
    <div class="as-body selectable"></div>
    <div class="as-sections"></div>
  `;
  node.el = el;
  node.bodyEl = el.querySelector(".as-body");
  node.bodyEl.dataset.nodeId = id;

  if (isDive) {
    node.sectionsEl = el.querySelector(".as-sections");
    diveHost(parent).appendChild(el);
  } else {
    sideList.appendChild(el);
  }
  state.order.push(id);

  streamInto(node.bodyEl, node.body, () => applyMarks(id));

  registerMark(containerId, clean, kind, id);
  bloomAt(anchorRect(containerId, clean));

  setActive(id);
  updateStatus();
  requestAnimationFrame(() => el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" }));
  return node;
}

function addQuestion(question) {
  const clean = question.replace(/\s+/g, " ").trim();
  if (!clean) return null;
  const data = generateRoot(clean, state.lens);
  const id = "q" + ++state.counter;
  const node = {
    id,
    parentId: null,
    depth: 0,
    kind: "root",
    isRoot: true,
    anchor: clean,
    title: data.title,
    body: data.body,
    citations: data.citations,
    estReadSeconds: data.estReadSeconds,
    collapsed: false,
  };
  state.nodes.set(id, node);

  const el = document.createElement("section");
  el.className = "action-section question-section kind-root";
  el.dataset.id = id;
  el.dataset.depth = "0";
  el.innerHTML = `
    <header class="as-head">
      <button type="button" class="as-toggle" aria-expanded="true" aria-label="Collapse">▼</button>
      <span class="as-kind">Question</span>
      <button type="button" class="as-anchor">${escapeHtml(clean)}</button>
      <button type="button" class="as-remove" aria-label="Remove section">✕</button>
    </header>
    <div class="as-body selectable"></div>
    <div class="as-sections"></div>
  `;
  node.el = el;
  node.bodyEl = el.querySelector(".as-body");
  node.bodyEl.dataset.nodeId = id;
  node.sectionsEl = el.querySelector(".as-sections");
  readingSections.appendChild(el);
  state.order.push(id);

  streamInto(node.bodyEl, node.body, () => applyMarks(id));
  setActive(id);
  updateStatus();
  requestAnimationFrame(() => el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" }));
  return node;
}

function registerMark(containerId, anchor, kind, id) {
  const key = normalize(anchor);
  let rec = state.marks.find((m) => m.containerId === containerId && m.key === key);
  if (!rec) {
    rec = { containerId, key, anchor, kinds: new Set(), count: 0, ids: [] };
    state.marks.push(rec);
  }
  rec.kinds.add(kind);
  rec.count += 1;
  rec.ids.push(id);
  applyMarks(containerId);
}

function applyMarks(containerId) {
  const el = containerEl(containerId);
  if (!el) return;
  state.marks
    .filter((m) => m.containerId === containerId)
    .forEach((rec) => {
      let spans = Array.from(el.querySelectorAll(".anchor")).filter((s) => normalize(s.dataset.term) === rec.key);
      if (!spans.length) {
        const wrapped = wrapFirstOccurrence(el, rec.anchor);
        if (wrapped) spans = [wrapped];
      }
      spans.forEach((span) => decorateAnchor(span, rec));
    });
  highlightActive();
}

function wrapFirstOccurrence(root, text) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
  const target = text.toLowerCase();
  let node;
  while ((node = walker.nextNode())) {
    const idx = node.data.toLowerCase().indexOf(target);
    if (idx === -1) continue;
    const range = document.createRange();
    range.setStart(node, idx);
    range.setEnd(node, idx + text.length);
    const span = document.createElement("span");
    span.className = "anchor";
    span.dataset.term = node.data.substr(idx, text.length);
    try {
      range.surroundContents(span);
      return span;
    } catch (e) {
      return null;
    }
  }
  return null;
}

function decorateAnchor(span, rec) {
  span.classList.add("branched");
  span.dataset.count = String(rec.count);
  const kinds = Array.from(rec.kinds);
  const last = kinds[kinds.length - 1];
  let icon = span.querySelector(".anchor-icon");
  if (!icon) {
    icon = document.createElement("span");
    icon.className = "anchor-icon";
    icon.setAttribute("role", "button");
    icon.tabIndex = 0;
    span.appendChild(icon);
  }
  const ordered = KIND_ORDER.filter((k) => rec.kinds.has(k));
  icon.textContent = Array.from(new Set(ordered.map((k) => KIND_LOC[k]))).join("") || "•";
  icon.dataset.kind = last;
  const where = [
    ordered.includes("dive") ? "below" : null,
    ordered.some((k) => KIND_LOC[k] === "→") ? "on the side" : null,
    ordered.includes("note") ? "in your notebook" : null,
  ].filter(Boolean).join(" and ");
  const summary = `${rec.count} action${rec.count > 1 ? "s" : ""} — ${kinds.join(", ")}`;
  icon.setAttribute("aria-label", `${summary}${where ? ` (opens ${where})` : ""}`);
  icon.title = `${summary}${where ? ` · opens ${where}` : ""}`;
}

function highlightActive() {
  document.querySelectorAll(".anchor.active").forEach((a) => a.classList.remove("active"));
  const node = state.nodes.get(state.activeId);
  if (!node || node.isRoot) return;
  const el = containerEl(node.parentId);
  if (!el) return;
  const key = normalize(node.anchor);
  Array.from(el.querySelectorAll(".anchor"))
    .filter((s) => normalize(s.dataset.term) === key)
    .forEach((s) => s.classList.add("active"));
}

function setActive(id) {
  if (!state.nodes.has(id)) return;
  state.activeId = id;
  renderSide();
  renderTrail();
  highlightActive();
}

function toggleSection(node) {
  node.collapsed = !node.collapsed;
  node.el.classList.toggle("collapsed", node.collapsed);
  const btn = node.el.querySelector(".as-toggle");
  btn.setAttribute("aria-expanded", String(!node.collapsed));
  btn.textContent = node.collapsed ? "▶" : "▼";
}

function focusSection(id) {
  const node = state.nodes.get(id);
  if (!node) return;
  if (node.collapsed) toggleSection(node);
  setActive(id);
  node.el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
  node.el.classList.add("flash");
  setTimeout(() => node.el.classList.remove("flash"), 900);
}

function descendantIds(id) {
  const ids = [id];
  const stack = [id];
  while (stack.length) {
    const cur = stack.pop();
    state.order.forEach((oid) => {
      const n = state.nodes.get(oid);
      if (n && n.parentId === cur) {
        ids.push(oid);
        stack.push(oid);
      }
    });
  }
  return ids;
}

function removeSection(node) {
  const ids = descendantIds(node.id);
  const els = ids.map((id) => state.nodes.get(id)).filter(Boolean).map((n) => n.el);
  ids.forEach((id) => state.nodes.delete(id));
  state.order = state.order.filter((id) => !ids.includes(id));
  els.forEach((el) => el && el.remove());
  if (!state.nodes.has(state.activeId)) state.activeId = node.parentId || state.rootId;
  updateStatus();
  renderSide();
  renderTrail();
  highlightActive();
}

function updateActions() {
  const count = state.order.filter((id) => {
    const node = state.nodes.get(id);
    return node && !node.isRoot && node.kind !== "dive";
  }).length;
  actionCount.textContent = String(count);
  actionsEmpty.hidden = count > 0;
}

function renderSide() {
  state.order.forEach((id) => {
    const node = state.nodes.get(id);
    if (!node || !node.el) return;
    node.el.classList.toggle("active", id === state.activeId);
  });
  updateActions();
}

function chainOf(id) {
  const chain = [];
  let node = state.nodes.get(id);
  while (node) {
    chain.unshift(node);
    node = node.parentId ? state.nodes.get(node.parentId) : null;
  }
  return chain;
}

function renderTrail() {
  trailEl.innerHTML = "";
  const chain = chainOf(state.activeId);
  const base = chain[0];
  const root = document.createElement("button");
  root.type = "button";
  root.className = "crumb crumb-root" + (base && base.id === state.activeId ? " crumb-current" : "");
  root.textContent = base ? truncate(base.anchor, 26) : "Question";
  root.title = base ? base.anchor : "Question";
  root.addEventListener("click", () => {
    const target = base && base.el ? base.el : document.querySelector(".reading");
    target.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  });
  trailEl.appendChild(root);

  chain
    .filter((n) => n !== base)
    .forEach((node) => {
      const sep = document.createElement("span");
      sep.className = "crumb-sep";
      sep.textContent = "›";
      trailEl.appendChild(sep);
      const crumb = document.createElement("button");
      crumb.type = "button";
      crumb.className = "crumb" + (node.id === state.activeId ? " crumb-current" : "");
      crumb.textContent = truncate(node.anchor, 26);
      crumb.title = node.anchor;
      crumb.addEventListener("click", () => focusSection(node.id));
      trailEl.appendChild(crumb);
    });
}

function rootOf(id) {
  let node = state.nodes.get(id);
  while (node && !node.isRoot) node = node.parentId ? state.nodes.get(node.parentId) : null;
  return node || state.nodes.get(state.rootId);
}

function updateStatus() {
  const n = state.order.filter((id) => {
    const node = state.nodes.get(id);
    return node && !node.isRoot;
  }).length;
  statusBranches.textContent = `${n} action${n === 1 ? "" : "s"}`;
  const root = rootOf(state.activeId);
  if (root) statusMeta.textContent = `≈ ${Math.max(1, Math.round(root.estReadSeconds / 60))} min read`;
}

function resultsFor(containerId, text) {
  const key = normalize(text);
  const rec = state.marks.find((m) => m.containerId === containerId && m.key === key);
  return rec ? rec.ids.filter((id) => state.nodes.has(id)) : [];
}

function renderToolbarResults(containerId, text) {
  const ids = resultsFor(containerId, text);
  toolbarResults.innerHTML = "";
  toolbarResults.hidden = ids.length === 0;
  if (!ids.length) return;
  const label = document.createElement("p");
  label.className = "toolbar-results-label";
  label.textContent = ids.length === 1 ? "Opens here" : `${ids.length} results`;
  toolbarResults.appendChild(label);
  ids.forEach((id) => {
    const node = state.nodes.get(id);
    const row = document.createElement("button");
    row.type = "button";
    row.className = "toolbar-result";
    row.setAttribute("role", "menuitem");
    row.dataset.kind = node.kind;
    row.innerHTML = `
      <span class="tr-loc" data-kind="${escapeAttr(node.kind)}" aria-hidden="true">${KIND_LOC[node.kind] || "•"}</span>
      <span class="tr-kind">${escapeHtml(KIND_LABELS[node.kind] || node.kind)}</span>
      <span class="tr-anchor">“${escapeHtml(node.anchor)}”</span>
    `;
    row.addEventListener("click", () => {
      hideToolbar();
      focusSection(id);
    });
    toolbarResults.appendChild(row);
  });
}

function showToolbar(text, rect, containerId) {
  state.toolbarContext = { text, containerId };
  toolbarPreview.textContent = truncate(text, 60);
  renderToolbarResults(containerId, text);
  toolbar.hidden = false;
  const tb = toolbar.getBoundingClientRect();
  let left = rect.left + rect.width / 2 - tb.width / 2;
  left = Math.max(12, Math.min(left, window.innerWidth - tb.width - 12));
  let top = rect.top - tb.height - 10;
  if (top < 12) top = rect.bottom + 10;
  toolbar.style.left = left + "px";
  toolbar.style.top = top + "px";
}

function hideToolbar() {
  toolbar.hidden = true;
  toolbarResults.hidden = true;
  state.toolbarContext = null;
}

function performAction(kind) {
  const ctx = state.toolbarContext;
  if (!ctx) return;
  if (kind === "note") saveNote(ctx.text, ctx.containerId);
  else createSection(ctx.containerId, ctx.text, kind);
  hideToolbar();
}

function saveNote(text, containerId) {
  const node = state.nodes.get(containerId);
  const context = node ? (node.isRoot ? readingTitle.textContent : node.title) : readingTitle.textContent;
  state.notes.unshift({ id: "n" + Date.now(), text: text.trim(), context });
  renderNotes();
  updateNoteCount();
  toast("Saved to notebook");
}

function updateNoteCount() {
  noteCount.textContent = String(state.notes.length);
}

function renderNotes() {
  noteList.innerHTML = "";
  notesEmpty.hidden = state.notes.length > 0;
  notesExport.hidden = state.notes.length === 0;
  state.notes.forEach((note) => {
    const li = document.createElement("li");
    li.className = "note";
    li.innerHTML = `<p class="note-text">“${escapeHtml(note.text)}”</p><p class="note-context">from <b>${escapeHtml(note.context)}</b></p>`;
    const del = document.createElement("button");
    del.type = "button";
    del.className = "note-del";
    del.textContent = "Remove";
    del.addEventListener("click", () => {
      state.notes = state.notes.filter((n) => n.id !== note.id);
      renderNotes();
      updateNoteCount();
    });
    li.appendChild(del);
    noteList.appendChild(li);
  });
}

function exportNotes() {
  const lines = ["# My Qriously trail", ""];
  chainOf(state.activeId).forEach((node) => {
    lines.push(`- ${node.anchor}`);
  });
  lines.push("", "## Saved notes", "");
  state.notes.forEach((n) => lines.push(`- “${n.text}” — from ${n.context}`));
  const text = lines.join("\n");
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => toast("Outline copied"), () => toast("Could not copy"));
  } else {
    toast("Outline ready");
  }
}

function startReader(question) {
  state.question = question;
  home.hidden = true;
  reader.hidden = false;
  lensChip.hidden = false;
  lensChipText.textContent = formatLens();
  composer.hidden = false;
  composerInput.value = question;

  state.nodes.clear();
  state.order = [];
  state.marks = [];
  state.activeId = null;
  state.counter = 0;
  readingSections.innerHTML = "";
  sideList.innerHTML = "";
  actionsEmpty.hidden = false;
  actionCount.textContent = "0";

  const rootNode = {
    id: "root",
    parentId: null,
    depth: 0,
    kind: "root",
    anchor: question,
    title: question,
    isRoot: true,
    el: document.querySelector(".reading"),
    sectionsEl: readingSections,
    bodyEl: readingBody,
    estReadSeconds: estimateReadSeconds(SEED_ROOT.body),
  };
  state.nodes.set("root", rootNode);
  state.rootId = "root";

  readingTitle.textContent = question;
  readingBody.dataset.nodeId = "root";
  readingMeta.textContent = "streaming…";
  streamInto(readingBody, SEED_ROOT.body, () => {
    readingMeta.textContent = "3 sources · verified overview";
    applyMarks("root");
  });

  renderTrail();
  updateActions();
  updateStatus();
  window.scrollTo({ top: 0, behavior: "auto" });
}

function openLens(question) {
  state.question = question;
  lensQuestion.textContent = "“" + question + "”";
  lensOverlay.hidden = false;
  lensOverlay.querySelectorAll(".lens-field").forEach((field) => {
    const key = field.dataset.field;
    field.querySelectorAll(".seg button").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.value === state.lens[key]);
    });
  });
}

function closeLens() {
  lensOverlay.hidden = true;
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem("qriously-lumen-theme", theme);
  } catch (e) {}
}

function initTheme() {
  let saved = null;
  try {
    saved = localStorage.getItem("qriously-lumen-theme");
  } catch (e) {}
  if (saved) return setTheme(saved);
  setTheme(window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
}

homeForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = homeInput.value.trim();
  if (!value) return homeInput.focus();
  openLens(value);
});

composerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = composerInput.value.trim();
  if (!value) return composerInput.focus();
  composerInput.value = "";
  addQuestion(value);
  toast("New question · " + formatLens());
});

document.querySelectorAll(".home-samples button").forEach((btn) => {
  btn.addEventListener("click", () => {
    homeInput.value = btn.dataset.q;
    openLens(btn.dataset.q);
  });
});

lensOverlay.querySelectorAll(".seg button").forEach((btn) => {
  btn.addEventListener("click", () => {
    const field = btn.closest(".lens-field").dataset.field;
    state.lens[field] = btn.dataset.value;
    btn.closest(".seg").querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
    lensChipText.textContent = formatLens();
  });
});

$("lensStart").addEventListener("click", () => {
  closeLens();
  startReader(state.question);
});
$("lensSkip").addEventListener("click", () => {
  closeLens();
  startReader(state.question);
});
lensChip.addEventListener("click", () => openLens(state.question));

toolbar.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => performAction(btn.dataset.act));
});

document.addEventListener("mouseup", (event) => {
  if (toolbar.contains(event.target)) return;
  if (event.target.closest && event.target.closest(".overlay, .notebook")) return;
  setTimeout(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;
    const text = selection.toString().trim();
    if (text.length < 2 || text.length > 120) return;
    const range = selection.getRangeAt(0);
    const start = range.startContainer;
    const host = start.nodeType === 1 ? start : start.parentElement;
    const container = host && host.closest("[data-node-id]");
    if (!container || !container.contains(range.endContainer)) return;
    showToolbar(text, range.getBoundingClientRect(), container.dataset.nodeId);
  }, 0);
});

document.addEventListener("mousedown", (event) => {
  if (!toolbar.hidden && !toolbar.contains(event.target)) hideToolbar();
});

document.addEventListener("click", (event) => {
  const icon = event.target.closest(".anchor-icon");
  if (icon) {
    event.preventDefault();
    event.stopPropagation();
    const span = icon.closest(".anchor");
    const container = span.closest("[data-node-id]");
    const ids = resultsFor(container.dataset.nodeId, span.dataset.term);
    if (ids.length > 1) showToolbar(span.dataset.term, span.getBoundingClientRect(), container.dataset.nodeId);
    else if (ids.length === 1) focusSection(ids[0]);
    return;
  }
  const anchor = event.target.closest(".anchor");
  if (anchor) {
    const container = anchor.closest("[data-node-id]");
    if (container) showToolbar(anchor.dataset.term, anchor.getBoundingClientRect(), container.dataset.nodeId);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (!toolbar.hidden) return hideToolbar();
    if (!notebook.hidden) return (notebook.hidden = true);
  }
  const el = document.activeElement;
  if ((event.key === "Enter" || event.key === " ") && el && (el.classList.contains("anchor-icon") || el.classList.contains("anchor"))) {
    event.preventDefault();
    el.click();
  }
});

function handleSectionClick(event) {
  const nodeEl = event.target.closest(".action-section, .side-card");
  if (!nodeEl) return;
  const node = state.nodes.get(nodeEl.dataset.id);
  if (!node) return;
  if (event.target.closest(".as-toggle")) return toggleSection(node);
  if (event.target.closest(".as-remove")) return removeSection(node);
  if (event.target.closest(".as-anchor")) return focusSection(node.id);
}

readingSections.addEventListener("click", handleSectionClick);
sideList.addEventListener("click", handleSectionClick);

themeBtn.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
notesBtn.addEventListener("click", () => (notebook.hidden = !notebook.hidden));
notesClose.addEventListener("click", () => (notebook.hidden = true));
notesExport.addEventListener("click", exportNotes);

$("newBtn").addEventListener("click", () => {
  if (reader.hidden) {
    homeInput.value = "";
    homeInput.focus();
  } else {
    composerInput.value = "";
    composerInput.focus();
  }
});

initTheme();
renderNotes();
updateNoteCount();

const params = new URLSearchParams(location.search);
if (params.has("demo")) {
  startReader(SEED_QUESTION);
  const d1 = createSection("root", "Rayleigh scattering", "dive");
  createSection("root", "Rayleigh scattering", "define");
  createSection("root", "nitrogen", "eli5");
  createSection(d1.id, "wavelength", "example");
  const d2 = createSection(d1.id, "violet", "dive");
  createSection(d2.id, "eyes", "dive");
}

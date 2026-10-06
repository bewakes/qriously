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
const actionList = $("actionList");
const actionCount = $("actionCount");
const actionsEmpty = $("actionsEmpty");
const actionPrev = $("actionPrev");
const actionNext = $("actionNext");
const actionExpand = $("actionExpand");
const statusMeta = $("statusMeta");
const statusBranches = $("statusBranches");
const toolbar = $("toolbar");
const toolbarPreview = $("toolbarPreview");
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
const motesLayer = $("motes");

const KIND_GLYPHS = { dive: "↓", eli5: "◔", example: "❖", define: "≡", note: "★" };

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

function setEnergy(value) {
  document.documentElement.style.setProperty("--energy", value.toFixed(2));
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
  state.order.push(id);

  const el = document.createElement("section");
  el.className = `action-section kind-${kind}`;
  el.dataset.id = id;
  el.dataset.depth = String(depth);
  el.innerHTML = `
    <header class="as-head">
      <button type="button" class="as-toggle" aria-expanded="true" aria-label="Collapse">▾</button>
      <span class="as-kind">${escapeHtml(KIND_LABELS[kind] || kind)}</span>
      <button type="button" class="as-anchor">“${escapeHtml(clean)}”</button>
      <span class="as-depth">L${depth}</span>
      <button type="button" class="as-remove" aria-label="Remove section">✕</button>
    </header>
    <div class="as-body selectable"></div>
    <div class="as-sections"></div>
  `;
  node.el = el;
  node.bodyEl = el.querySelector(".as-body");
  node.sectionsEl = el.querySelector(".as-sections");
  node.bodyEl.dataset.nodeId = id;

  const host = parent.isRoot ? readingSections : parent.sectionsEl;
  host.appendChild(el);

  streamInto(node.bodyEl, node.body, () => applyMarks(id));

  registerMark(containerId, clean, kind, id);
  bloomAt(anchorRect(containerId, clean));
  setEnergy(Math.min(1, 0.32 + state.order.length * 0.09));

  setActive(id);
  updateActions();
  updateStatus();
  requestAnimationFrame(() => el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" }));
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
  icon.textContent = KIND_GLYPHS[last] || "•";
  icon.dataset.kind = last;
  icon.setAttribute("aria-label", `${rec.count} action${rec.count > 1 ? "s" : ""}: ${kinds.join(", ")}`);
  icon.title = `${rec.count} action${rec.count > 1 ? "s" : ""} — ${kinds.join(", ")}`;
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
  renderActions();
  renderTrail();
  highlightActive();
}

function toggleSection(node) {
  node.collapsed = !node.collapsed;
  node.el.classList.toggle("collapsed", node.collapsed);
  const btn = node.el.querySelector(".as-toggle");
  btn.setAttribute("aria-expanded", String(!node.collapsed));
  btn.textContent = node.collapsed ? "▸" : "▾";
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

function removeSection(node) {
  const ids = [node.id];
  node.el.querySelectorAll(".action-section").forEach((c) => ids.push(c.dataset.id));
  ids.forEach((id) => state.nodes.delete(id));
  state.order = state.order.filter((id) => !ids.includes(id));
  node.el.remove();
  if (!state.nodes.has(state.activeId)) state.activeId = node.parentId;
  updateActions();
  updateStatus();
  renderActions();
  renderTrail();
  highlightActive();
}

function navigate(dir) {
  const i = state.order.indexOf(state.activeId);
  if (i === -1) {
    if (state.order.length) focusSection(state.order[state.order.length - 1]);
    return;
  }
  const next = state.order[i + dir];
  if (next) focusSection(next);
}

function updateActions() {
  actionCount.textContent = String(state.order.length);
  actionsEmpty.hidden = state.order.length > 0;
}

function renderActions() {
  actionList.innerHTML = "";
  state.order.forEach((id) => {
    const node = state.nodes.get(id);
    const li = document.createElement("li");
    li.className = "action-row kind-" + node.kind + (id === state.activeId ? " active" : "");
    li.style.setProperty("--depth", String(node.depth - 1));
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "action-row-main";
    btn.innerHTML = `
      <span class="ar-icon" aria-hidden="true">${KIND_GLYPHS[node.kind] || "•"}</span>
      <span class="ar-anchor">“${escapeHtml(node.anchor)}”</span>
      <span class="ar-depth">L${node.depth}</span>
    `;
    btn.addEventListener("click", () => focusSection(id));
    li.appendChild(btn);
    actionList.appendChild(li);
  });
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
  const root = document.createElement("button");
  root.type = "button";
  root.className = "crumb crumb-root";
  root.textContent = "Question";
  root.addEventListener("click", () => document.querySelector(".reading").scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" }));
  trailEl.appendChild(root);

  chainOf(state.activeId)
    .filter((n) => !n.isRoot)
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

function updateStatus() {
  const n = state.order.length;
  statusBranches.textContent = `${n} action${n === 1 ? "" : "s"}`;
  if (state.rootId) {
    const root = state.nodes.get(state.rootId);
    statusMeta.textContent = `≈ ${Math.max(1, Math.round(root.estReadSeconds / 60))} min read`;
  }
}

function showToolbar(text, rect, containerId) {
  state.toolbarContext = { text, containerId };
  toolbarPreview.textContent = truncate(text, 60);
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
  actionList.innerHTML = "";
  actionsEmpty.hidden = false;
  actionCount.textContent = "0";
  setEnergy(0.32);

  const rootNode = {
    id: "root",
    parentId: null,
    depth: 0,
    kind: "root",
    anchor: question,
    title: question,
    isRoot: true,
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
  renderActions();
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

function initMotes() {
  if (reduce || !motesLayer) return;
  for (let i = 0; i < 16; i += 1) {
    const mote = document.createElement("span");
    mote.className = "mote";
    mote.style.left = Math.random() * 100 + "vw";
    mote.style.bottom = "-10px";
    mote.style.width = mote.style.height = 2 + Math.random() * 4 + "px";
    mote.style.animationDuration = 14 + Math.random() * 18 + "s";
    mote.style.animationDelay = -Math.random() * 20 + "s";
    mote.style.background = ["var(--accent)", "var(--accent-2)", "var(--accent-3)"][i % 3];
    motesLayer.appendChild(mote);
  }
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
  composerInput.value = value;
  startReader(value);
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
    const rec = state.marks.find((m) => m.containerId === container.dataset.nodeId && normalize(m.anchor) === normalize(span.dataset.term));
    if (rec && rec.ids.length) focusSection(rec.ids[rec.ids.length - 1]);
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

readingSections.addEventListener("click", (event) => {
  const nodeEl = event.target.closest(".action-section");
  if (!nodeEl) return;
  const node = state.nodes.get(nodeEl.dataset.id);
  if (!node) return;
  if (event.target.closest(".as-toggle")) return toggleSection(node);
  if (event.target.closest(".as-remove")) return removeSection(node);
  if (event.target.closest(".as-anchor")) return focusSection(node.id);
});

actionPrev.addEventListener("click", () => navigate(-1));
actionNext.addEventListener("click", () => navigate(1));
actionExpand.addEventListener("click", () => {
  const expanded = $("actions").classList.toggle("expanded");
  actionExpand.setAttribute("aria-pressed", String(expanded));
});

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
initMotes();

const params = new URLSearchParams(location.search);
if (params.has("demo")) {
  startReader(SEED_QUESTION);
  createSection("root", "Rayleigh scattering", "dive");
  createSection("root", "nitrogen", "eli5");
  const c = createSection("root", "Rayleigh scattering", "example");
  createSection(c.id, "violet", "dive");
  createSection(c.id, "wavelength", "define");
}

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
const toolbarAskForm = $("toolbarAskForm");
const toolbarAskInput = $("toolbarAskInput");
const lensOverlay = $("lensOverlay");
const lensQuestion = $("lensQuestion");
const lensChip = $("lensChip");
const lensChipText = $("lensChipText");
const creditMeter = $("creditMeter");
const creditValue = $("creditValue");
const connBadge = $("connBadge");
const themeBtn = $("themeBtn");
const notesBtn = $("notesBtn");
const logoutBtn = $("logoutBtn");
const noteCount = $("noteCount");
const notebook = $("notebook");
const notesClose = $("notesClose");
const notesEmpty = $("notesEmpty");
const noteList = $("noteList");
const notesExport = $("notesExport");
const noteCompose = $("noteCompose");
const noteComposeInput = $("noteComposeInput");
const toastEl = $("toast");
const historyBtn = $("historyBtn");
const brandHome = $("brandHome");
const confirmOverlay = $("confirmOverlay");
const confirmTitle = $("confirmTitle");
const confirmMessage = $("confirmMessage");
const confirmCancel = $("confirmCancel");
const confirmDelete = $("confirmDelete");
const login = $("login");
const loginForm = $("loginForm");
const loginStartBtn = $("loginStartBtn");
const loginEmail = $("loginEmail");
const loginCode = $("loginCode");
const loginEmailStep = $("loginEmailStep");
const loginCodeStep = $("loginCodeStep");
const loginStatus = $("loginStatus");
const loginBack = $("loginBack");

const WAIT_MESSAGES = ["Considering…", "Cross-referencing…", "Composing the reply…"];
let waitTimer = null;

const KIND_LOC = { dive: "↓", ask: "→", eli5: "→", example: "→", define: "→", note: "★" };
const KIND_ORDER = ["dive", "ask", "eli5", "example", "define", "note"];
const SIDE_KINDS = new Set(["ask", "eli5", "example", "define"]);
const MAX_SELECTION = 800;

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
  threadId: null,
  credits: null,
  creditsKnown: false,
  pendingCharges: new Set(),
  threads: [],
  historyCursor: null,
  historyDone: true,
};

const content = window.QriouslyContent;

function sessionParam() {
  return new URLSearchParams(location.search).get("session");
}

function setSessionUrl(id, mode) {
  if (new URLSearchParams(location.search).has("demo")) return;
  try {
    const url = new URL(location.href);
    if (id) url.searchParams.set("session", id);
    else url.searchParams.delete("session");
    const method = mode === "replace" ? "replaceState" : "pushState";
    history[method]({ session: id || null }, "", url.pathname + url.search);
  } catch (e) {}
}

function uuid() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

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

function nodeLabel(node) {
  return node.kind === "ask" ? node.title : node.anchor;
}

function askHeading(refText, question) {
  return (
    `<span class="as-q">${escapeHtml(question)}</span>` +
    `<span class="as-ref">“${escapeHtml(refText)}”</span>`
  );
}

function inlineBody(text) {
  let out = "";
  let last = 0;
  const re = /\*\*(.+?)\*\*/g;
  let match;
  while ((match = re.exec(text))) {
    out += escapeHtml(text.slice(last, match.index));
    out += `<span class="anchor" data-term="${escapeAttr(match[1])}">${escapeHtml(match[1])}</span>`;
    last = re.lastIndex;
  }
  return out + escapeHtml(text.slice(last));
}

function renderBody(raw) {
  const lines = String(raw).split("\n");
  const html = [];
  let paragraph = [];
  let listTag = null;

  const closeList = () => {
    if (listTag) {
      html.push(`</${listTag}>`);
      listTag = null;
    }
  };
  const flushParagraph = () => {
    if (paragraph.length) {
      html.push(`<p>${inlineBody(paragraph.join(" "))}</p>`);
      paragraph = [];
    }
  };

  lines.forEach((line) => {
    const text = line.trim();
    if (!text) {
      flushParagraph();
      closeList();
      return;
    }
    const bullet = /^[-*]\s+(.*)$/.exec(text);
    const numbered = /^\d+[.)]\s+(.*)$/.exec(text);
    const item = bullet ? bullet[1] : numbered ? numbered[1] : null;
    if (item !== null) {
      flushParagraph();
      const tag = bullet ? "ul" : "ol";
      if (listTag !== tag) {
        closeList();
        html.push(`<${tag}>`);
        listTag = tag;
      }
      html.push(`<li>${inlineBody(item)}</li>`);
      return;
    }
    closeList();
    paragraph.push(text);
  });

  flushParagraph();
  closeList();
  return html.join("");
}

function startBodyStream(el) {
  let raw = "";
  let frame = null;
  el.classList.add("streaming");
  el.textContent = "";
  const paint = () => {
    frame = null;
    el.innerHTML = renderBody(raw);
  };
  return {
    token(text) {
      raw += text;
      if (!frame) frame = requestAnimationFrame(paint);
    },
    finish() {
      if (frame) {
        cancelAnimationFrame(frame);
        frame = null;
      }
      el.classList.remove("streaming");
      el.innerHTML = renderBody(raw);
      return raw;
    },
    fail() {
      if (frame) {
        cancelAnimationFrame(frame);
        frame = null;
      }
      el.classList.remove("streaming");
    },
  };
}

function setCredits(balance, meta) {
  if (typeof balance !== "number") return;
  state.credits = balance;
  state.creditsKnown = true;
  creditValue.textContent = String(balance);
  creditMeter.hidden = false;
  creditMeter.classList.toggle("low", balance <= 30);
  creditMeter.classList.toggle("reused", Boolean(meta && meta.cacheHit));
  creditMeter.classList.toggle("pending", state.pendingCharges.size > 0);
  if (balance > 0) creditMeter.classList.remove("empty");
}

function onGenerationMeta(meta, nodeId) {
  if (!state.creditsKnown || !meta) return;
  if (nodeId) state.pendingCharges.add(nodeId);
  setCredits(Math.max(0, state.credits - (meta.cost || 0)));
}

function onGenerationUsage(usage, nodeId) {
  if (!usage) return;
  if (nodeId) state.pendingCharges.delete(nodeId);
  setCredits(usage.balance, { cacheHit: usage.cache_hit });
  if (usage.cache_hit) {
    toast(`Reused an earlier answer · ${usage.credits_charged} credits`);
  }
}

function reconcilePending(nodeId) {
  if (!state.pendingCharges.delete(nodeId)) return;
  setCredits(state.credits);
  content.balance().then((serverBalance) => {
    if (typeof serverBalance === "number") setCredits(serverBalance);
  });
}

function showConnection(mode) {
  const live = mode === "api";
  connBadge.hidden = false;
  connBadge.textContent = live ? "Live" : "Offline · sample";
  connBadge.classList.toggle("live", live);
}

function errorKind(err) {
  if (err && err.status === 402) return "credits";
  if (err && err.status === 422) return "blocked";
  if (err && err.code) return "upstream";
  return "offline";
}

function renderNodeError(node, err) {
  const kind = errorKind(err);
  const messages = {
    credits: "You're out of credits for now.",
    blocked: "I can't help with that one.",
    upstream: "The answer service couldn't respond just now.",
    offline: "Couldn't reach the server. Check your connection and try again.",
  };
  node.bodyEl.innerHTML = `
    <div class="node-error" data-kind="${kind}">
      <p>${escapeHtml(messages[kind])}</p>
      ${kind === "blocked" ? "" : '<button type="button" class="node-retry">Try again</button>'}
    </div>
  `;
  const retry = node.bodyEl.querySelector(".node-retry");
  if (retry) {
    retry.addEventListener("click", () => {
      node.bodyEl.innerHTML = "";
      node.status = "streaming";
      fillContent(node);
    });
  }
  if (kind === "blocked") toast("Can't help with that one.");
  if (kind === "credits") {
    creditMeter.hidden = false;
    creditMeter.classList.add("empty");
    toast("Out of credits.");
  }
}

function toast(message) {
  toastEl.textContent = message;
  toastEl.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toastEl.classList.remove("show"), 2400);
}

function confirmAction(opts) {
  const options = opts || {};
  confirmTitle.textContent = options.title || "Delete?";
  confirmMessage.textContent = options.message || "This can't be undone.";
  confirmDelete.textContent = options.confirmLabel || "Delete";
  confirmOverlay.hidden = false;
  confirmCancel.focus();
  return new Promise((resolve) => {
    const done = (result) => {
      confirmOverlay.hidden = true;
      confirmDelete.removeEventListener("click", onConfirm);
      confirmCancel.removeEventListener("click", onCancel);
      confirmOverlay.removeEventListener("click", onBackdrop);
      document.removeEventListener("keydown", onKey);
      resolve(result);
    };
    const onConfirm = () => done(true);
    const onCancel = () => done(false);
    const onBackdrop = (event) => {
      if (event.target === confirmOverlay) done(false);
    };
    const onKey = (event) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        done(false);
      }
    };
    confirmDelete.addEventListener("click", onConfirm);
    confirmCancel.addEventListener("click", onCancel);
    confirmOverlay.addEventListener("click", onBackdrop);
    document.addEventListener("keydown", onKey);
  });
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

function createSection(containerId, anchor, kind, options) {
  const parent = state.nodes.get(containerId);
  if (!parent) return null;
  const clean = anchor.replace(/\s+/g, " ").trim();
  if (!clean) return null;

  const preset = options && options.preset;
  const depth = parent.depth + 1;
  const id = "a" + ++state.counter;
  const question = options && options.question ? options.question : null;
  const node = {
    id,
    parentId: containerId,
    depth,
    kind,
    anchor: clean,
    question,
    title: preset && preset.title ? preset.title : kind === "ask" && question ? question : clean,
    body: "",
    citations: [],
    estReadSeconds: 0,
    collapsed: false,
    status: "streaming",
    remoteId: preset ? preset.id : null,
    idemKey: uuid(),
  };
  state.nodes.set(id, node);

  const isInline = kind === "dive";
  const el = document.createElement(isInline ? "section" : "li");
  el.className = isInline ? `action-section kind-${kind}` : `side-card kind-${kind}`;
  el.dataset.id = id;
  el.dataset.depth = String(depth);
  const heading = kind === "ask" ? askHeading(clean, node.title) : `“${escapeHtml(clean)}”`;
  el.innerHTML = `
    <header class="as-head">
      <button type="button" class="as-toggle" aria-expanded="true" aria-label="Collapse">▼</button>
      <span class="as-kind">${escapeHtml(KIND_LABELS[kind] || kind)}</span>
      <button type="button" class="as-anchor" title="Collapse or expand">${heading}</button>
      <button type="button" class="as-source" aria-label="Show where this appears in the text" title="Show in text">↩</button>
      <button type="button" class="as-remove" aria-label="Remove section">✕</button>
    </header>
    <div class="as-body selectable"></div>
    <div class="as-sections"></div>
  `;
  node.el = el;
  node.bodyEl = el.querySelector(".as-body");
  node.bodyEl.dataset.nodeId = id;

  if (isInline) {
    node.sectionsEl = el.querySelector(".as-sections");
    diveHost(parent).appendChild(el);
  } else {
    sideList.appendChild(el);
  }
  state.order.push(id);

  registerMark(containerId, clean, kind, id);

  if (preset) {
    node.body = preset.body || "";
    node.citations = preset.citations || [];
    node.estReadSeconds = preset.est_read_seconds || 0;
    node.status = "done";
    node.bodyEl.innerHTML = renderBody(node.body);
    if (preset.collapsed) toggleSection(node);
    updateStatus();
    return node;
  }

  bloomAt(anchorRect(containerId, clean));
  setActive(id);
  updateStatus();
  requestAnimationFrame(() => el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" }));
  fillContent(node);
  return node;
}

function createAsk(containerId, anchor, question) {
  const clean = question.replace(/\s+/g, " ").trim();
  if (!clean) return null;
  return createSection(containerId, anchor, "ask", { question: clean });
}

function addQuestion(question, options) {
  const clean = question.replace(/\s+/g, " ").trim();
  if (!clean) return null;
  const preset = options && options.preset;
  const isFollowup = Boolean(options && options.followup);
  const parentId = isFollowup && state.rootId ? state.rootId : null;
  const id = "q" + ++state.counter;
  const node = {
    id,
    parentId,
    depth: 0,
    kind: isFollowup ? "followup" : "root",
    isRoot: !isFollowup,
    anchor: clean,
    question: clean,
    title: preset && preset.title ? preset.title : clean,
    body: "",
    citations: [],
    estReadSeconds: 0,
    collapsed: false,
    status: "streaming",
    remoteId: preset ? preset.id : null,
    idemKey: uuid(),
  };
  state.nodes.set(id, node);

  const el = document.createElement("section");
  el.className = "action-section question-section kind-" + node.kind;
  el.dataset.id = id;
  el.dataset.depth = "0";
  el.innerHTML = `
    <header class="as-head">
      <button type="button" class="as-toggle" aria-expanded="true" aria-label="Collapse">▼</button>
      <span class="as-kind">${isFollowup ? "Follow-up" : "Question"}</span>
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

  if (preset) {
    node.body = preset.body || "";
    node.citations = preset.citations || [];
    node.estReadSeconds = preset.est_read_seconds || 0;
    node.status = "done";
    node.bodyEl.innerHTML = renderBody(node.body);
    if (preset.collapsed) toggleSection(node);
    updateStatus();
    return node;
  }

  setActive(id);
  updateStatus();
  requestAnimationFrame(() => el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" }));
  fillContent(node);
  return node;
}

function startWaitNote() {
  stopWaitNote();
  let i = 0;
  readingMeta.textContent = WAIT_MESSAGES[0];
  if (reduce) return;
  waitTimer = setInterval(() => {
    i = (i + 1) % WAIT_MESSAGES.length;
    readingMeta.textContent = WAIT_MESSAGES[i];
  }, 1100);
}

function stopWaitNote() {
  if (waitTimer) {
    clearInterval(waitTimer);
    waitTimer = null;
  }
}

function updateReadingMeta(node) {
  const mins = Math.max(1, Math.round((node.estReadSeconds || 0) / 60));
  readingMeta.textContent = `≈ ${mins} min read`;
}

function fillContent(node) {
  const view = startBodyStream(node.bodyEl);
  const parentNode = node.isRoot ? null : state.nodes.get(node.parentId);
  const hooks = {
    onToken: view.token,
    onMeta: (meta) => onGenerationMeta(meta, node.id),
    onUsage: (usage) => onGenerationUsage(usage, node.id),
    idempotencyKey: node.idemKey,
  };
  const context = {
    threadId: state.threadId,
    parentRemoteId: parentNode ? parentNode.remoteId : null,
    parent: parentNode,
    anchor: node.anchor,
    kind: node.kind,
    question: node.question,
    lens: state.lens,
    idempotencyKey: node.idemKey,
  };
  const run =
    node.isRoot && !state.threadId
      ? content.startRoot(node.question, state.lens, hooks)
      : content.streamBranch(context, hooks);

  run
    .then((data) => {
      node.body = view.finish();
      node.status = "done";
      if (data.title && node.kind === "ask") {
        node.title = data.title;
        const anchorBtn = node.el.querySelector(".as-anchor");
        if (anchorBtn) anchorBtn.innerHTML = askHeading(node.anchor, data.title);
      }
      node.citations = data.citations || [];
      node.estReadSeconds = data.estReadSeconds || 0;
      node.remoteId = data.nodeId || node.remoteId;
      if (node.isRoot && data.threadId) {
        state.threadId = data.threadId;
        setSessionUrl(data.threadId, "push");
        loadHistory(true);
      } else {
        renderHistory();
      }
      applyMarks(node.id);
      updateStatus();
      renderTrail();
      if (node.isRoot) {
        stopWaitNote();
        updateReadingMeta(node);
      }
    })
    .catch((err) => {
      view.fail();
      node.status = "error";
      reconcilePending(node.id);
      if (node.isRoot) {
        stopWaitNote();
        readingMeta.textContent = "";
      }
      renderNodeError(node, err);
    });
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
    ordered.some((k) => KIND_LOC[k] === "↓") ? "below" : null,
    ordered.some((k) => KIND_LOC[k] === "→") ? "on the side" : null,
    ordered.includes("note") ? "in your notebook" : null,
  ].filter(Boolean).join(" and ");
  const summary = `${rec.count} action${rec.count > 1 ? "s" : ""} — ${kinds.join(", ")}`;
  icon.setAttribute("aria-label", `${summary}${where ? ` (opens ${where})` : ""}`);
  icon.title = `${summary}${where ? ` · opens ${where}` : ""}`;
}

function clearHighlight() {
  document.querySelectorAll(".anchor.active").forEach((a) => a.classList.remove("active"));
  document.querySelectorAll(".action-section.active, .side-card.active").forEach((el) => el.classList.remove("active"));
}

function clearSelection() {
  const selection = window.getSelection();
  if (selection) selection.removeAllRanges();
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
  if (node.collapsed && state.activeId === node.id) clearHighlight();
}

function expandAncestors(id) {
  let node = state.nodes.get(id);
  node = node && node.parentId ? state.nodes.get(node.parentId) : null;
  while (node) {
    if (node.collapsed) toggleSection(node);
    node = node.parentId ? state.nodes.get(node.parentId) : null;
  }
}

function focusSection(id) {
  const node = state.nodes.get(id);
  if (!node) return;
  expandAncestors(id);
  if (node.collapsed) toggleSection(node);
  setActive(id);
  node.el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
  node.el.classList.add("flash");
  setTimeout(() => node.el.classList.remove("flash"), 900);
}

function focusSource(node) {
  expandAncestors(node.id);
  const el = containerEl(node.parentId);
  if (!el) return;
  const key = normalize(node.anchor);
  const span = Array.from(el.querySelectorAll(".anchor")).find((s) => normalize(s.dataset.term) === key);
  if (!span) return;
  setActive(node.id);
  span.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
  span.classList.add("flash");
  setTimeout(() => span.classList.remove("flash"), 900);
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

function requestRemoveSection(node) {
  const isQuestion = node.kind === "followup";
  const label = nodeLabel(node) || node.anchor || "this section";
  confirmAction({
    title: isQuestion ? "Remove follow-up?" : "Remove section?",
    message: `Remove “${truncate(label, 80)}” and everything nested under it? This can't be undone.`,
    confirmLabel: "Remove",
  }).then((confirmed) => {
    if (confirmed) removeSection(node);
  });
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
    return node && SIDE_KINDS.has(node.kind);
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

function isBase(node) {
  return Boolean(node) && (node.isRoot || node.kind === "followup");
}

function chainOf(id) {
  const chain = [];
  let node = state.nodes.get(id);
  while (node) {
    chain.unshift(node);
    if (isBase(node)) break;
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
      crumb.textContent = truncate(nodeLabel(node), 26);
      crumb.title = nodeLabel(node);
      crumb.addEventListener("click", () => focusSection(node.id));
      trailEl.appendChild(crumb);
    });
}

function rootOf(id) {
  let node = state.nodes.get(id);
  while (node && !isBase(node)) node = node.parentId ? state.nodes.get(node.parentId) : null;
  return node || state.nodes.get(state.rootId);
}

function updateStatus() {
  const n = state.order.filter((id) => {
    const node = state.nodes.get(id);
    return node && !isBase(node);
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
    row.dataset.kind = node.kind;
    row.innerHTML = `
      <span class="tr-loc" data-kind="${escapeAttr(node.kind)}" aria-hidden="true">${KIND_LOC[node.kind] || "•"}</span>
      <span class="tr-kind">${escapeHtml(KIND_LABELS[node.kind] || node.kind)}</span>
      <span class="tr-anchor">${node.kind === "ask" ? escapeHtml(nodeLabel(node)) : "“" + escapeHtml(nodeLabel(node)) + "”"}</span>
    `;
    row.addEventListener("click", () => {
      hideToolbar();
      focusSection(id);
    });
    toolbarResults.appendChild(row);
  });
}

function showToolbar(text, rect, containerId, opts) {
  const noteOnly = !!(opts && opts.noteOnly);
  state.toolbarContext = { text, containerId, noteOnly };
  toolbarPreview.textContent = truncate(text, 60);
  toolbar.classList.toggle("note-only", noteOnly);
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
  toolbarAskInput.value = "";
  state.toolbarContext = null;
  clearSelection();
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
  const note = { id: "n" + Date.now(), text: text.trim(), context, remoteId: null };
  state.notes.unshift(note);
  renderNotes();
  updateNoteCount();
  toast("Saved to notebook");

  const remoteNodeId = node ? node.remoteId : null;
  if (state.threadId && remoteNodeId) {
    content.saveNote({ threadId: state.threadId, remoteNodeId, text: note.text, context }).then((saved) => {
      if (saved && saved.id) note.remoteId = saved.id;
    });
  }
}

function addFreeNote(text) {
  const clean = text.trim();
  if (!clean) return;
  const context = state.question || readingTitle.textContent || "this session";
  const note = { id: "n" + Date.now(), text: clean, context, remoteId: null };
  state.notes.unshift(note);
  renderNotes();
  updateNoteCount();
  toast("Note added");
  if (state.threadId) {
    content.saveNote({ threadId: state.threadId, text: clean, context }).then((saved) => {
      if (saved && saved.id) note.remoteId = saved.id;
    });
  }
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
      if (note.remoteId) content.deleteNote(note.remoteId);
    });
    li.appendChild(del);
    noteList.appendChild(li);
  });
}

function exportNotes() {
  const lines = ["# My Qriously trail", ""];
  chainOf(state.activeId).forEach((node) => {
    lines.push(`- ${nodeLabel(node)}`);
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
  state.threadId = null;
  setSessionUrl(null, "replace");
  home.hidden = true;
  reader.hidden = false;
  historyBtn.hidden = false;
  applyHistoryOpen();
  lensChip.hidden = false;
  lensChipText.textContent = formatLens();
  composer.hidden = false;
  composerInput.value = "";

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
    isRoot: true,
    anchor: question,
    question,
    title: question,
    el: document.querySelector(".reading"),
    sectionsEl: readingSections,
    bodyEl: readingBody,
    body: "",
    citations: [],
    estReadSeconds: 0,
    collapsed: false,
    status: "streaming",
    remoteId: null,
    idemKey: uuid(),
  };
  state.nodes.set("root", rootNode);
  state.rootId = "root";

  readingTitle.textContent = question;
  readingBody.dataset.nodeId = "root";
  startWaitNote();

  renderTrail();
  updateActions();
  updateStatus();
  window.scrollTo({ top: 0, behavior: "auto" });
  fillContent(rootNode);
}

function restoreSession(snapshot) {
  const nodes = (snapshot && snapshot.nodes) || [];
  if (!nodes.length) return false;
  stopWaitNote();
  const thread = snapshot.thread || {};
  if (thread.lens && Object.keys(thread.lens).length) state.lens = thread.lens;
  state.question = thread.title || nodes[0].title || "";

  home.hidden = true;
  reader.hidden = false;
  historyBtn.hidden = false;
  applyHistoryOpen();
  lensChip.hidden = false;
  lensChipText.textContent = formatLens();
  composer.hidden = false;
  composerInput.value = "";

  state.nodes.clear();
  state.order = [];
  state.marks = [];
  state.notes = [];
  state.pendingCharges.clear();
  state.activeId = null;
  state.counter = 0;
  readingSections.innerHTML = "";
  sideList.innerHTML = "";
  actionsEmpty.hidden = false;
  actionCount.textContent = "0";
  state.threadId = thread.id || null;

  const spanById = new Map();
  (snapshot.spans || []).forEach((span) => spanById.set(span.id, span));
  const remoteToLocal = new Map();

  const first = nodes.find((n) => !n.parent_id) || nodes[0];
  const rootNode = {
    id: "root",
    parentId: null,
    depth: 0,
    kind: first.kind || "root",
    isRoot: true,
    anchor: first.anchor_text || first.title || state.question,
    question: first.title || state.question,
    title: first.title || state.question,
    el: document.querySelector(".reading"),
    sectionsEl: readingSections,
    bodyEl: readingBody,
    body: first.body || "",
    citations: first.citations || [],
    estReadSeconds: first.est_read_seconds || 0,
    collapsed: false,
    status: "done",
    remoteId: first.id,
    idemKey: "",
  };
  state.nodes.set("root", rootNode);
  state.rootId = "root";
  readingTitle.textContent = rootNode.title;
  readingBody.dataset.nodeId = "root";
  readingBody.innerHTML = renderBody(rootNode.body);
  updateReadingMeta(rootNode);
  remoteToLocal.set(first.id, "root");

  nodes
    .filter((n) => n.id !== first.id)
    .forEach((spec) => {
      const preset = {
        id: spec.id,
        title: spec.title,
        body: spec.body,
        citations: spec.citations,
        est_read_seconds: spec.est_read_seconds,
        collapsed: Boolean(spec.collapsed),
      };
      const anchor = spec.anchor_text || spec.title || spec.kind;
      let created;
      if (spec.parent_id && spec.kind !== "followup") {
        const parentLocal = remoteToLocal.get(spec.parent_id);
        if (!parentLocal) return;
        created = createSection(parentLocal, anchor, spec.kind, {
          preset: { ...preset, collapsed: true },
          question: spec.kind === "ask" ? spec.title : null,
        });
      } else {
        created = addQuestion(spec.title || anchor || "Question", {
          preset,
          followup: spec.kind === "followup",
        });
      }
      if (created) remoteToLocal.set(spec.id, created.id);
    });

  (snapshot.notes || []).forEach((note) => {
    const span = spanById.get(note.span_id);
    const localId = span ? remoteToLocal.get(span.source_node_id) : null;
    const localNode = localId ? state.nodes.get(localId) : null;
    const context =
      note.context ||
      (localNode ? (localNode.isRoot ? rootNode.title : localNode.title) : thread.title || "this session");
    state.notes.push({ id: note.id, text: note.text, context, remoteId: note.id });
  });

  setActive("root");
  renderTrail();
  updateActions();
  updateStatus();
  renderSide();
  renderNotes();
  updateNoteCount();
  window.scrollTo({ top: 0, behavior: "auto" });
  return true;
}

function relTime(iso) {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (isNaN(then)) return "";
  const secs = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (secs < 60) return "just now";
  const mins = Math.round(secs / 60);
  if (mins < 60) return mins + "m ago";
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return hrs + "h ago";
  const days = Math.round(hrs / 24);
  if (days < 30) return days + "d ago";
  return new Date(iso).toLocaleDateString();
}

function historyPref() {
  try {
    return localStorage.getItem("qriously-history-open");
  } catch (e) {
    return null;
  }
}

function applyHistoryOpen() {
  const pref = historyPref();
  const open = pref === null ? !reader.hidden : pref === "1";
  document.body.classList.toggle("history-collapsed", !open);
  historyBtn.setAttribute("aria-expanded", String(open));
}

function setHistoryOpen(open) {
  try {
    localStorage.setItem("qriously-history-open", open ? "1" : "0");
  } catch (e) {}
  applyHistoryOpen();
}

function historyItemHtml(thread) {
  const current = thread.id === state.threadId ? " current" : "";
  return (
    `<li class="history-row">` +
    `<button type="button" class="history-item${current}" data-id="${escapeAttr(thread.id)}">` +
    `<span class="hi-title">${escapeHtml(thread.title || "Untitled session")}</span>` +
    `<span class="hi-meta">${escapeHtml(relTime(thread.updated_at || thread.created_at))}</span>` +
    `</button>` +
    `<button type="button" class="history-del" data-del="${escapeAttr(thread.id)}" aria-label="Delete session" title="Delete">✕</button>` +
    `</li>`
  );
}

function deleteSession(id) {
  if (!id) return;
  const thread = state.threads.find((t) => t.id === id);
  const label = thread && thread.title ? thread.title : "this session";
  confirmAction({
    title: "Delete session?",
    message: `Delete “${truncate(label, 80)}”? This can't be undone.`,
    confirmLabel: "Delete",
  }).then((confirmed) => {
    if (!confirmed) return;
    content.deleteThread(id).then((ok) => {
      if (!ok) return toast("Couldn't delete that session");
      state.threads = state.threads.filter((t) => t.id !== id);
      if (id === state.threadId) {
        resetToHome();
        setSessionUrl(null, "replace");
      }
      renderHistory();
      toast("Session deleted");
    });
  });
}

function renderHistory() {
  const html = state.threads.map(historyItemHtml).join("");
  document.querySelectorAll(".history-list").forEach((list) => {
    list.innerHTML = html;
  });
  document.querySelectorAll(".history-empty").forEach((el) => {
    el.hidden = state.threads.length > 0;
  });
  document.querySelectorAll(".history-more").forEach((el) => {
    el.hidden = state.historyDone || state.threads.length === 0;
  });
  home.classList.toggle("has-history", state.threads.length > 0);
  historyBtn.hidden = reader.hidden && state.threads.length === 0;
}

function loadHistory(reset) {
  if (reset) {
    state.threads = [];
    state.historyCursor = null;
    state.historyDone = false;
  }
  if (state.historyDone && !reset) return Promise.resolve();
  return content.listThreads(state.historyCursor).then((page) => {
    const results = (page && page.results) || [];
    results.forEach((thread) => {
      if (!state.threads.some((t) => t.id === thread.id)) state.threads.push(thread);
    });
    const next = page && page.next;
    let cursor = null;
    if (next) {
      try {
        cursor = new URL(next, location.origin).searchParams.get("cursor");
      } catch (e) {
        cursor = null;
      }
    }
    state.historyCursor = cursor;
    state.historyDone = !cursor;
    renderHistory();
  });
}

function openThread(id) {
  if (!id) return;
  if (id === state.threadId) {
    setHistoryOpen(true);
    renderHistory();
    return;
  }
  content.restoreThread(id).then((snapshot) => {
    if (snapshot && snapshot.nodes && snapshot.nodes.length) {
      restoreSession(snapshot);
      setSessionUrl(id, "push");
      toast("Session loaded");
    } else {
      toast("Couldn't load that session");
    }
    renderHistory();
  });
}

function resetToHome() {
  state.threadId = null;
  stopWaitNote();
  hideToolbar();
  state.question = "";
  state.nodes.clear();
  state.order = [];
  state.marks = [];
  state.notes = [];
  state.pendingCharges.clear();
  state.activeId = null;
  state.rootId = null;
  readingSections.innerHTML = "";
  sideList.innerHTML = "";
  readingBody.innerHTML = "";
  readingTitle.textContent = "";
  composerInput.value = "";
  homeInput.value = "";
  reader.hidden = true;
  composer.hidden = true;
  historyBtn.hidden = true;
  lensChip.hidden = true;
  home.hidden = false;
  applyHistoryOpen();
  renderNotes();
  updateNoteCount();
  renderTrail();
  renderHistory();
  window.scrollTo({ top: 0, behavior: "auto" });
  homeInput.focus();
}

function newSession() {
  resetToHome();
  setSessionUrl(null, "push");
}

function applyRoute() {
  const id = sessionParam();
  if (!id) {
    if (!reader.hidden) resetToHome();
    return;
  }
  if (id === state.threadId) return;
  content.restoreThread(id).then((snapshot) => {
    if (snapshot && snapshot.nodes && snapshot.nodes.length) restoreSession(snapshot);
    else resetToHome();
    renderHistory();
  });
}

window.addEventListener("popstate", applyRoute);

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
  addQuestion(value, { followup: true });
  toast("Follow-up · " + formatLens());
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

toolbar.querySelectorAll(".toolbar-actions button").forEach((btn) => {
  btn.addEventListener("click", () => performAction(btn.dataset.act));
});

toolbarAskForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const ctx = state.toolbarContext;
  const question = toolbarAskInput.value.trim();
  if (!ctx || !question) return;
  createAsk(ctx.containerId, ctx.text, question);
  hideToolbar();
});

document.addEventListener("mouseup", (event) => {
  if (toolbar.contains(event.target)) return;
  if (event.target.closest && event.target.closest(".overlay, .notebook, .as-head, button")) return;
  setTimeout(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) return;
    const text = selection.toString().trim();
    if (text.length < 2) return;
    const range = selection.getRangeAt(0);
    const start = range.startContainer;
    const host = start.nodeType === 1 ? start : start.parentElement;
    if (host && host.closest(".as-head, button, .toolbar, .composer, .topbar, .trail")) return;
    const container = host && host.closest("[data-node-id]");
    if (!container || !container.contains(range.endContainer)) return;
    const noteOnly = text.length > MAX_SELECTION;
    showToolbar(text, range.getBoundingClientRect(), container.dataset.nodeId, { noteOnly });
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
    return;
  }
  if (event.target.closest(".action-section, .side-card, .toolbar, .notebook, .overlay, .composer, .topbar, .trail, .home")) return;
  clearHighlight();
});

document.addEventListener("keydown", (event) => {
  if (!confirmOverlay.hidden) return;
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
  if (event.target.closest(".as-remove")) return requestRemoveSection(node);
  if (event.target.closest(".as-source")) return focusSource(node);
  if (event.target.closest(".as-toggle, .as-anchor")) return toggleSection(node);
}

readingSections.addEventListener("click", handleSectionClick);
sideList.addEventListener("click", handleSectionClick);

themeBtn.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
notesBtn.addEventListener("click", () => (notebook.hidden = !notebook.hidden));
logoutBtn.addEventListener("click", async () => {
  logoutBtn.disabled = true;
  await content.logout();
  location.reload();
});
notesClose.addEventListener("click", () => (notebook.hidden = true));
notesExport.addEventListener("click", exportNotes);
noteCompose.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = noteComposeInput.value.trim();
  if (!value) return noteComposeInput.focus();
  noteComposeInput.value = "";
  addFreeNote(value);
});

$("newBtn").addEventListener("click", newSession);
brandHome.addEventListener("click", (event) => {
  event.preventDefault();
  if (document.body.classList.contains("guest")) return;
  if (reader.hidden) homeInput.focus();
  else newSession();
});
document.addEventListener("click", (event) => {
  const del = event.target.closest(".history-del");
  if (del) return deleteSession(del.dataset.del);
  const item = event.target.closest(".history-item");
  if (item) return openThread(item.dataset.id);
  if (event.target.closest(".history-new")) return newSession();
  if (event.target.closest(".history-more")) return loadHistory(false);
  if (event.target.closest(".history-collapse")) return setHistoryOpen(false);
});
historyBtn.addEventListener("click", () => setHistoryOpen(document.body.classList.contains("history-collapsed")));

let loginPhase = "email";

function setLoginStatus(text, kind) {
  loginStatus.textContent = text || "";
  loginStatus.dataset.kind = kind || "";
}

function showLogin(reason) {
  document.body.classList.add("guest");
  home.hidden = true;
  reader.hidden = true;
  composer.hidden = true;
  login.hidden = false;
  loginStartBtn.hidden = false;
  loginForm.hidden = true;
  loginEmailStep.hidden = false;
  loginCodeStep.hidden = true;
  loginPhase = "email";
  loginEmail.value = "";
  loginCode.value = "";
  $("newBtn").hidden = true;
  notesBtn.hidden = true;
  logoutBtn.hidden = true;
  if (reason === "offline") {
    setLoginStatus("Server unreachable — explore a sample below.", "error");
  } else if (reason === "claim_required") {
    setLoginStatus("Your current session is saved — sign in to move it into your account.");
  }
  loginStartBtn.focus();
}

loginStartBtn.addEventListener("click", () => {
  loginStartBtn.hidden = true;
  loginForm.hidden = false;
  loginPhase = "email";
  loginEmail.focus();
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const email = loginEmail.value.trim();
  if (loginPhase === "email") {
    if (!email) return loginEmail.focus();
    setLoginStatus("Sending code…");
    try {
      const res = await content.loginStart(email);
      loginPhase = "code";
      loginEmailStep.hidden = true;
      loginCodeStep.hidden = false;
      loginCode.focus();
      setLoginStatus(
        res && res.requires_code === false
          ? "Signing in…"
          : "Code sent — check the server console."
      );
    } catch (err) {
      setLoginStatus("Couldn't reach the server — try a sample below.", "error");
    }
    return;
  }
  const code = loginCode.value.trim();
  if (!code) return loginCode.focus();
  setLoginStatus("Signing in…");
  try {
    await content.login(email, code);
    location.reload();
  } catch (err) {
    setLoginStatus("That code didn't work. Try again.", "error");
  }
});

loginBack.addEventListener("click", () => {
  loginPhase = "email";
  loginCodeStep.hidden = true;
  loginEmailStep.hidden = false;
  setLoginStatus("");
  loginEmail.focus();
});

document.querySelectorAll(".demo-card").forEach((card) => {
  card.addEventListener("click", () => {
    const url = new URL(location.href);
    url.search = "";
    url.searchParams.set("demo", "1");
    if (card.dataset.demo) url.searchParams.set("q", card.dataset.demo);
    location.href = url.toString();
  });
});

initTheme();
renderNotes();
updateNoteCount();
applyHistoryOpen();
renderHistory();

const params = new URLSearchParams(location.search);

function seedDemo() {
  startReader(SEED_QUESTION);
  const d1 = createSection("root", "Rayleigh scattering", "dive");
  createSection("root", "Rayleigh scattering", "define");
  createSection("root", "nitrogen", "eli5");
  if (!d1) return;
  createSection(d1.id, "wavelength", "example");
  const d2 = createSection(d1.id, "violet", "dive");
  if (d2) createSection(d2.id, "eyes", "dive");
}

content.init().then((info) => {
  if (info.mode === "api") {
    showConnection("api");
    setCredits(info.balance);
    loadHistory(true);
    const urlSession = sessionParam();
    if (urlSession && !params.has("demo")) {
      content.restoreThread(urlSession).then((snapshot) => {
        if (snapshot && snapshot.nodes && snapshot.nodes.length) {
          restoreSession(snapshot);
        } else {
          setSessionUrl(null, "replace");
          toast("That session is no longer available");
        }
        renderHistory();
      });
    }
  } else if (params.has("demo")) {
    showConnection("mock");
    const demoQuestion = params.get("q");
    if (demoQuestion) startReader(demoQuestion);
    else seedDemo();
  } else if (info.mode === "guest") {
    showLogin(info.reason);
  } else {
    showConnection("mock");
  }
});

/* Content adapter: chooses the real API or the offline mock and presents one
   streaming interface to the app. Mock behavior lives in content.js behind its
   original generateRoot/generateNode/generateAsk signatures. */

(function () {
  "use strict";

  var API = window.QriouslyAPI;
  var params = new URLSearchParams(location.search);
  var mode = "mock";
  var readyPromise = null;

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function boot() {
    if (params.has("demo")) {
      mode = "mock";
      return Promise.resolve({ mode: mode, balance: null, reason: "demo" });
    }
    return API.me()
      .then(function () {
        return API.balance();
      })
      .then(function (wallet) {
        mode = "api";
        return { mode: mode, balance: wallet.balance, reason: "live" };
      })
      .catch(function (err) {
        mode = "mock";
        return { mode: mode, balance: null, reason: err && err.message };
      });
  }

  function init() {
    if (!readyPromise) readyPromise = boot();
    return readyPromise;
  }

  function mockStream(body, onToken) {
    return new Promise(function (resolve) {
      if (prefersReducedMotion()) {
        onToken(body);
        resolve();
        return;
      }
      var words = String(body).split(" ");
      var i = 0;
      function step() {
        var prev = i;
        i = Math.min(words.length, i + 2);
        onToken((prev > 0 ? " " : "") + words.slice(prev, i).join(" "));
        if (i < words.length) setTimeout(step, 16);
        else resolve();
      }
      setTimeout(step, 40);
    });
  }

  function startRootMock(question, lens, hooks) {
    var data = window.generateRoot(question, lens);
    return mockStream(data.body, hooks.onToken).then(function () {
      if (hooks.onDone) {
        hooks.onDone({ title: data.title, est_read_seconds: data.estReadSeconds });
      }
      return {
        threadId: null,
        nodeId: null,
        cacheHit: false,
        cost: 0,
        balance: null,
        title: data.title,
        citations: data.citations || [],
        estReadSeconds: data.estReadSeconds,
      };
    });
  }

  function startRootApi(question, lens, hooks) {
    return API.post(
      "/threads",
      { question: question, lens: lens },
      hooks.idempotencyKey
    ).then(function (created) {
      return API.stream(created.stream_url, hooks).then(function (result) {
        return {
          threadId: created.thread.id,
          nodeId: created.node_id,
          cacheHit: created.cache_hit,
          cost: created.cost,
          balance: result.usage ? result.usage.balance : created.balance,
          title: (result.done && result.done.title) || question,
          citations: [],
          estReadSeconds: result.done ? result.done.est_read_seconds : 0,
        };
      });
    });
  }

  function streamBranchMock(ctx, hooks) {
    var data;
    if (ctx.kind === "ask") {
      data = window.generateAsk(ctx.parent, ctx.anchor, ctx.question, ctx.lens);
    } else if (ctx.kind === "root") {
      data = window.generateRoot(ctx.question || ctx.anchor, ctx.lens);
    } else {
      data = window.generateNode(ctx.parent, ctx.anchor, ctx.kind, ctx.lens);
    }
    return mockStream(data.body, hooks.onToken).then(function () {
      if (hooks.onDone) {
        hooks.onDone({ title: data.title, est_read_seconds: data.estReadSeconds });
      }
      return {
        nodeId: null,
        cacheHit: false,
        cost: 0,
        balance: null,
        title: data.title,
        citations: data.citations || [],
        estReadSeconds: data.estReadSeconds,
      };
    });
  }

  function streamBranchApi(ctx, hooks) {
    var body = {
      thread_id: ctx.threadId,
      parent_node_id: ctx.parentRemoteId || null,
      kind: ctx.kind,
      lens: ctx.lens,
    };
    if (ctx.kind === "ask" || ctx.kind === "root") {
      body.question = ctx.question || ctx.anchor;
    }
    if (ctx.kind !== "root") body.span = { text: ctx.anchor };

    return API.post("/generate", body, ctx.idempotencyKey).then(function (descriptor) {
      return API.stream(descriptor.stream_url, hooks).then(function (result) {
        return {
          nodeId: descriptor.node_id,
          cacheHit: descriptor.cache_hit,
          cost: descriptor.cost,
          balance: result.usage ? result.usage.balance : descriptor.balance,
          title: (result.done && result.done.title) || ctx.anchor,
          citations: [],
          estReadSeconds: result.done ? result.done.est_read_seconds : 0,
        };
      });
    });
  }

  function startRoot(question, lens, hooks) {
    return init().then(function () {
      return mode === "api"
        ? startRootApi(question, lens, hooks)
        : startRootMock(question, lens, hooks);
    });
  }

  function streamBranch(ctx, hooks) {
    return init().then(function () {
      return mode === "api"
        ? streamBranchApi(ctx, hooks)
        : streamBranchMock(ctx, hooks);
    });
  }

  /* List the device user's sessions (api only), newest activity first.
     Resolves to { results: [], next: null } offline or on failure. */
  function listThreads(cursor) {
    return init().then(function () {
      if (mode !== "api") return { results: [], next: null };
      var path = "/threads" + (cursor ? "?cursor=" + encodeURIComponent(cursor) : "");
      return API.get(path).catch(function () {
        return { results: [], next: null };
      });
    });
  }

  /* Load a persisted thread snapshot (api only). Resolves to null when offline
     or when the thread is gone, so the caller can fall back to the home screen. */
  function restoreThread(threadId) {
    return init().then(function () {
      if (mode !== "api" || !threadId) return null;
      return API.get("/threads/" + encodeURIComponent(threadId)).catch(function () {
        return null;
      });
    });
  }

  /* Persist a note (api only). Resolves to the saved note, or null in the mock. */
  function saveNote(payload) {
    return init().then(function () {
      if (mode !== "api") return null;
      return API.post("/threads/" + encodeURIComponent(payload.threadId) + "/notes", {
        source_node_id: payload.remoteNodeId,
        text: payload.text,
        context: payload.context,
      }).catch(function () {
        return null;
      });
    });
  }

  function deleteNote(noteId) {
    return init().then(function () {
      if (mode !== "api" || !noteId) return true;
      return API.del("/notes/" + encodeURIComponent(noteId))
        .then(function () {
          return true;
        })
        .catch(function () {
          return false;
        });
    });
  }

  window.QriouslyContent = {
    init: init,
    startRoot: startRoot,
    streamBranch: streamBranch,
    listThreads: listThreads,
    restoreThread: restoreThread,
    saveNote: saveNote,
    deleteNote: deleteNote,
    getMode: function () {
      return mode;
    },
    mockStream: mockStream,
  };
})();

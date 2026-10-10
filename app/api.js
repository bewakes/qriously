/* Low-level Qriously API client: device auth, REST, and the SSE reader.
   Plain global (no modules) so the app keeps working without a build step. */

(function () {
  "use strict";

  var DEFAULT_BASE = "http://localhost:8000/api/v1";
  var TOKEN_KEY = "qriously-device-token";
  var params = new URLSearchParams(location.search);

  function resolveBase() {
    if (window.QRIOUSLY_API_BASE) return window.QRIOUSLY_API_BASE;
    var override = params.get("api");
    if (override) return override.replace(/\/$/, "");
    if (location.protocol.indexOf("http") === 0 && location.port === "8000") {
      return location.origin + "/api/v1";
    }
    return DEFAULT_BASE;
  }

  var base = resolveBase();
  var origin = base.replace(/\/api\/v1\/?$/, "");
  var token = readToken();

  function readToken() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch (e) {
      return null;
    }
  }

  function storeToken(value) {
    token = value;
    try {
      localStorage.setItem(TOKEN_KEY, value);
    } catch (e) {
      /* storage unavailable (private mode) — in-memory only */
    }
  }

  function clearToken() {
    token = null;
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch (e) {
      /* ignore */
    }
  }

  function hasToken() {
    return !!token;
  }

  function authHeaders(extra) {
    var headers = Object.assign({ "Content-Type": "application/json" }, extra || {});
    if (token) headers.Authorization = "Bearer " + token;
    return headers;
  }

  function parse(text) {
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (e) {
      return null;
    }
  }

  function apiError(status, body, fallback) {
    var err = new Error((body && (body.error || body.detail)) || fallback || "request_failed");
    err.status = status;
    err.body = body || null;
    return err;
  }

  async function request(method, path, body, extraHeaders) {
    var response = await fetch(base + path, {
      method: method,
      headers: authHeaders(extraHeaders),
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    var data = parse(await response.text());
    if (!response.ok) throw apiError(response.status, data, response.statusText);
    return data;
  }

  async function ensureAuth() {
    if (token) return token;
    var err = new Error("login_required");
    err.code = "login_required";
    err.status = 401;
    throw err;
  }

  async function loginStart(email) {
    return request("POST", "/auth/login/start", { email: email });
  }

  async function login(email, code) {
    var data = await request("POST", "/auth/login", { email: email, code: code });
    if (!data || !data.token) throw apiError(0, null, "login_failed");
    storeToken(data.token);
    return data;
  }

  async function logout() {
    try {
      if (token) await request("POST", "/auth/logout");
    } catch (e) {
      /* best effort — clear the local token regardless */
    }
    clearToken();
  }

  async function me() {
    await ensureAuth();
    return request("GET", "/me");
  }

  async function balance() {
    await ensureAuth();
    return request("GET", "/credits/balance");
  }

  async function get(path) {
    await ensureAuth();
    return request("GET", path);
  }

  async function post(path, body, idempotencyKey) {
    await ensureAuth();
    var headers = idempotencyKey ? { "Idempotency-Key": idempotencyKey } : null;
    return request("POST", path, body, headers);
  }

  async function del(path) {
    await ensureAuth();
    return request("DELETE", path);
  }

  async function probe(timeoutMs) {
    var controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = setTimeout(function () {
      if (controller) controller.abort();
    }, timeoutMs || 1500);
    try {
      var response = await fetch(origin + "/health/ready", {
        signal: controller ? controller.signal : undefined,
      });
      return response.ok;
    } finally {
      clearTimeout(timer);
    }
  }

  /* Read an SSE stream. `streamUrl` is the descriptor's absolute path
     (e.g. /api/v1/generate/<id>/stream). Resolves with { meta, done, usage }
     once the stream ends; throws a retryable error on an `error` event. */
  async function stream(streamUrl, handlers) {
    handlers = handlers || {};
    var url = /^https?:/.test(streamUrl) ? streamUrl : origin + streamUrl;
    var response = await fetch(url, { headers: authHeaders() });
    if (!response.ok) throw apiError(response.status, parse(await response.text()));
    if (!response.body || !response.body.getReader) {
      throw apiError(0, null, "streaming_unsupported");
    }

    var reader = response.body.getReader();
    var decoder = new TextDecoder();
    var buffer = "";
    var meta = null;
    var done = null;
    var usage = null;
    var error = null;

    function dispatch(block) {
      var event = "message";
      var data = "";
      block.split("\n").forEach(function (line) {
        if (line.indexOf("event:") === 0) event = line.slice(6).trim();
        else if (line.indexOf("data:") === 0) data += line.slice(5).trim();
      });
      if (!data) return;
      var payload = parse(data);
      if (!payload) return;
      if (event === "meta") {
        meta = payload;
        if (handlers.onMeta) handlers.onMeta(payload);
      } else if (event === "token") {
        if (handlers.onToken) handlers.onToken(payload.text || "");
      } else if (event === "done") {
        done = payload;
        if (handlers.onDone) handlers.onDone(payload);
      } else if (event === "usage") {
        usage = payload;
        if (handlers.onUsage) handlers.onUsage(payload);
      } else if (event === "error") {
        error = payload;
      }
    }

    while (true) {
      var step = await reader.read();
      if (step.done) break;
      buffer += decoder.decode(step.value, { stream: true });
      var blocks = buffer.split("\n\n");
      buffer = blocks.pop();
      blocks.forEach(dispatch);
    }
    if (buffer.trim()) dispatch(buffer);

    if (error) {
      var err = new Error(error.message || error.code || "generation_failed");
      err.code = error.code;
      err.retryable = error.retryable !== false;
      throw err;
    }
    return { meta: meta, done: done, usage: usage };
  }

  window.QriouslyAPI = {
    base: base,
    ensureAuth: ensureAuth,
    hasToken: hasToken,
    clearToken: clearToken,
    loginStart: loginStart,
    login: login,
    logout: logout,
    me: me,
    balance: balance,
    get: get,
    post: post,
    del: del,
    probe: probe,
    stream: stream,
  };
})();

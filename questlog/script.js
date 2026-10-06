const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const form = document.getElementById("askForm");
const ask = document.querySelector(".ask");
const input = document.getElementById("askInput");
const samples = document.getElementById("samples");
const response = document.getElementById("response");
const responseQ = document.getElementById("responseQ");
const responseNote = document.querySelector(".response-note");
const resetBtn = document.getElementById("responseReset");
const sparkleLayer = document.getElementById("sparkles");
const toast = document.getElementById("toast");
const toastText = document.getElementById("toastText");
const xpFill = document.getElementById("xpFill");
const xpText = document.getElementById("xpText");
const xpBar = document.getElementById("xpBar");
const lvlNum = document.getElementById("lvlNum");

const messages = ["Consulting the archives…", "Unrolling the scrolls…", "Rewriting the map…"];

let messageTimer = null;
let toastTimer = null;
let xp = 0;
let level = 1;

function setXp(value) {
  xp = Math.max(0, Math.min(100, value));
  xpFill.style.width = xp + "%";
  xpText.textContent = xp + " / 100 XP";
  xpBar.setAttribute("aria-valuenow", String(xp));
}

function gainXp(amount) {
  const before = xp;
  const next = before + amount;
  if (next >= 100) {
    level += 1;
    lvlNum.textContent = String(level);
    setXp(next - 100);
    showToast("Level up! Welcome to Scholar " + level + ".");
  } else {
    setXp(next);
    showToast("+" + amount + " XP · Quest accepted");
  }
}

function showToast(text) {
  toastText.textContent = text;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function sparkleBurst() {
  if (reduceMotion || !sparkleLayer) return;
  const rect = input.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  for (let i = 0; i < 16; i += 1) {
    const s = document.createElement("span");
    s.className = "sparkle";
    s.textContent = Math.random() > 0.5 ? "✦" : "✧";
    s.style.left = cx + "px";
    s.style.top = cy + "px";
    s.style.fontSize = (10 + Math.random() * 12).toFixed(0) + "px";
    s.style.setProperty("--x", (Math.random() - 0.5) * 360 + "px");
    s.style.setProperty("--y", (Math.random() - 1.1) * 260 + "px");
    s.style.animationDelay = (Math.random() * 0.15).toFixed(2) + "s";
    sparkleLayer.appendChild(s);
    s.addEventListener("animationend", () => s.remove());
  }
}

function submitQuestion(question) {
  const value = (question ?? input.value).trim();
  if (!value) {
    ask.classList.remove("shake");
    void ask.offsetWidth;
    ask.classList.add("shake");
    input.focus();
    return;
  }

  input.value = value;
  responseQ.textContent = value;
  response.hidden = false;
  sparkleBurst();
  gainXp(25);

  samples.style.transition = "opacity .4s ease, transform .4s ease";
  samples.style.opacity = "0";
  samples.style.transform = "translateY(-10px)";
  window.setTimeout(() => { samples.hidden = true; }, 400);

  clearTimeout(messageTimer);
  let i = 0;
  responseNote.textContent = messages[0];
  const tick = () => {
    i += 1;
    if (i < messages.length) {
      responseNote.textContent = messages[i];
      messageTimer = setTimeout(tick, 1000);
    } else {
      responseNote.textContent = "The archives have answered. Onward!";
    }
  };
  messageTimer = setTimeout(tick, 1000);

  response.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "nearest" });
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion();
});

document.querySelectorAll(".card").forEach((card) => {
  card.addEventListener("click", () => {
    input.value = card.dataset.q || "";
    submitQuestion(input.value);
  });
});

resetBtn.addEventListener("click", () => {
  clearTimeout(messageTimer);
  response.hidden = true;
  input.value = "";
  samples.hidden = false;
  requestAnimationFrame(() => {
    samples.style.opacity = "1";
    samples.style.transform = "translateY(0)";
  });
  input.focus();
});

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const form = document.getElementById("askForm");
const ask = document.querySelector(".ask");
const input = document.getElementById("askInput");
const samples = document.getElementById("samples");
const response = document.getElementById("response");
const responseQ = document.getElementById("responseQ");
const responseNote = document.querySelector(".response-note");
const resetBtn = document.getElementById("responseReset");
const confettiLayer = document.getElementById("confetti");

const colors = ["#ff6b5c", "#ffc93c", "#4cc3ff", "#9b6bff", "#43d9a3"];

const messages = [
  "Gathering the good stuff…",
  "Connecting the dots…",
  "Almost there…",
];

let messageTimer = null;

function burstConfetti() {
  if (reduceMotion || !confettiLayer) return;
  const count = 22;
  for (let i = 0; i < count; i += 1) {
    const piece = document.createElement("span");
    piece.className = "confetti-piece";
    const x = (Math.random() - 0.5) * 420;
    piece.style.left = 50 + (Math.random() - 0.5) * 30 + "%";
    piece.style.background = colors[(Math.random() * colors.length) | 0];
    piece.style.setProperty("--x", x + "px");
    piece.style.setProperty("--rot", Math.round(360 + Math.random() * 900) + "deg");
    piece.style.setProperty("--dur", (1.3 + Math.random() * 1.1).toFixed(2) + "s");
    piece.style.animationDelay = (Math.random() * 0.25).toFixed(2) + "s";
    if (Math.random() > 0.6) piece.style.borderRadius = "50%";
    confettiLayer.appendChild(piece);
    piece.addEventListener("animationend", () => piece.remove());
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
  burstConfetti();

  samples.style.transition = "opacity .4s ease, transform .4s ease";
  samples.style.opacity = "0";
  samples.style.transform = "translateY(-10px)";
  window.setTimeout(() => {
    samples.hidden = true;
  }, 400);

  clearTimeout(messageTimer);
  let i = 0;
  responseNote.textContent = messages[0];
  const tick = () => {
    i += 1;
    if (i < messages.length) {
      responseNote.textContent = messages[i];
      messageTimer = setTimeout(tick, 1000);
    } else {
      responseNote.textContent = "Ooh, good one. Let's find out together!";
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

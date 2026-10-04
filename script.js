const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const form = document.getElementById("askForm");
const ask = document.querySelector(".ask");
const input = document.getElementById("askInput");
const samples = document.getElementById("samples");
const response = document.getElementById("response");
const responseQ = document.getElementById("responseQ");
const responseNote = document.querySelector(".response-note");
const resetBtn = document.getElementById("responseReset");
const arrow = document.querySelector(".ask-btn svg");

const messages = [
  "Gathering the good stuff…",
  "Connecting the dots…",
  "Almost there…",
];

let messageTimer = null;

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

  ask.classList.remove("pulse");
  void ask.offsetWidth;
  ask.classList.add("pulse");

  if (arrow && !reduceMotion) {
    arrow.classList.remove("arrow-fly");
    void arrow.getBoundingClientRect();
    arrow.classList.add("arrow-fly");
  }

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
      responseNote.textContent = "Nice thread to pull. Let's find out together.";
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

if (!reduceMotion) {
  const canvas = document.getElementById("particles");
  const ctx = canvas.getContext("2d");
  const colors = ["#7c5cff", "#42e8e0", "#ffb454", "#ffffff"];
  let width = 0;
  let height = 0;
  let particles = [];
  const pointer = { x: 0, y: 0 };

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    seed();
  }

  function seed() {
    const count = Math.round(Math.min(80, (width * height) / 18000));
    particles = Array.from({ length: count }, () => {
      const depth = Math.random();
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        r: depth * 1.7 + 0.4,
        vx: (Math.random() - 0.5) * 0.12,
        vy: -(depth * 0.28 + 0.05),
        base: depth * 0.45 + 0.12,
        phase: Math.random() * Math.PI * 2,
        speed: 0.006 + Math.random() * 0.014,
        depth: depth,
        color: colors[(Math.random() * colors.length) | 0],
      };
    });
  }

  function frame() {
    ctx.clearRect(0, 0, width, height);
    for (const p of particles) {
      p.phase += p.speed;
      p.x += p.vx + (pointer.x - width / 2) * 0.00002 * (p.depth + 0.4);
      p.y += p.vy + (pointer.y - height / 2) * 0.00002 * (p.depth + 0.4);

      if (p.y < -12) { p.y = height + 12; p.x = Math.random() * width; }
      if (p.x < -12) p.x = width + 12;
      if (p.x > width + 12) p.x = -12;

      const alpha = p.base * (0.6 + 0.4 * Math.sin(p.phase));
      ctx.globalAlpha = alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(frame);
  }

  window.addEventListener("pointermove", (event) => {
    pointer.x = event.clientX;
    pointer.y = event.clientY;
  });

  window.addEventListener("resize", resize);
  resize();
  frame();
}

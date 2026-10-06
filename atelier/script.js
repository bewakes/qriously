const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const form = document.getElementById("askForm");
const ask = document.querySelector(".ask");
const input = document.getElementById("askInput");
const samples = document.getElementById("samples");
const response = document.getElementById("response");
const responseQ = document.getElementById("responseQ");
const responseNote = document.querySelector(".response-note");
const resetBtn = document.getElementById("responseReset");

const messages = ["Considering…", "Cross-referencing…", "Composing the reply…"];

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

  samples.style.transition = "opacity .45s ease, transform .45s ease";
  samples.style.opacity = "0";
  samples.style.transform = "translateY(-10px)";
  window.setTimeout(() => { samples.hidden = true; }, 450);

  clearTimeout(messageTimer);
  let i = 0;
  responseNote.textContent = messages[0];
  const tick = () => {
    i += 1;
    if (i < messages.length) {
      responseNote.textContent = messages[i];
      messageTimer = setTimeout(tick, 1100);
    } else {
      responseNote.textContent = "A worthy question. Let us find out together.";
    }
  };
  messageTimer = setTimeout(tick, 1100);

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

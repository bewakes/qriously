const SEED_QUESTION = "Why is the sky blue?";

const SEED_ROOT = {
  title: "Why is the sky blue?",
  body: "Sunlight looks white, but it is really a blend of every colour. As it reaches the **atmosphere**, it collides with molecules of **nitrogen** and **oxygen**. Those molecules scatter the shorter, bluer waves far more than the longer, red ones — a process called **Rayleigh scattering**. The scattered blue light then reaches your eyes from every direction at once, so the whole sky glows blue.",
};

const LIBRARY = {
  "rayleigh scattering": {
    dive: {
      title: "Rayleigh scattering, in detail",
      body: "Rayleigh scattering is the scattering of light by particles much smaller than the light's **wavelength**. Its strength climbs steeply as waves get shorter — roughly as the fourth power of frequency. That is why **violet** scatters even more than blue, yet the sky is not violet: our **eyes** are far more sensitive to blue, and the **sun** emits less violet to begin with. Long **red** waves barely scatter at all, which is why **sunsets** turn red and the Sun itself reddens near the **horizon**.",
      citations: 3,
    },
    eli5: {
      title: "Rayleigh scattering, simply",
      body: "Imagine sunlight as a stream of tiny balls, and the air as a room full of even tinier ones. Blue balls bounce off in every direction; red balls mostly fly straight through. So blue ends up filling the whole sky and reaching your eyes from everywhere.",
      citations: 1,
    },
    define: {
      title: "Rayleigh scattering",
      body: "Rayleigh scattering — the scattering of light by particles smaller than its wavelength. It affects short (blue) waves far more than long (red) ones, and it is why the sky is blue.",
      citations: 2,
    },
    example: {
      title: "A glass of milky water",
      body: "Put a drop of milk in a glass of water and shine a torch through it. From the side, the beam looks blue; look straight through the end and it glows orange. Same effect, tabletop-sized.",
      citations: 1,
    },
  },
  nitrogen: {
    dive: {
      title: "Nitrogen",
      body: "Nitrogen (N₂) makes up about 78% of the air. Its molecules are far smaller than the wavelength of visible light — exactly the size range where **Rayleigh scattering** is strongest.",
      citations: 2,
    },
    eli5: {
      title: "Nitrogen",
      body: "Air is mostly nitrogen: billions of teeny molecules that nudge sunlight around in every direction.",
      citations: 1,
    },
    define: {
      title: "Nitrogen",
      body: "Nitrogen — the most common gas in Earth's **atmosphere**, about 78% of the air you breathe.",
      citations: 1,
    },
  },
  oxygen: {
    dive: {
      title: "Oxygen",
      body: "Oxygen (O₂) is about 21% of the air. Like nitrogen, its molecules are small enough to scatter light in the **Rayleigh** regime, though it is not the main scatterer simply because there is less of it.",
      citations: 2,
    },
    define: {
      title: "Oxygen",
      body: "Oxygen — the second most common gas in air, about 21%, and the one we need to breathe.",
      citations: 1,
    },
  },
  wavelength: {
    dive: {
      title: "Wavelength",
      body: "Wavelength is the distance between one peak of a light wave and the next. Shorter waves look blue; longer ones look red. Scattering strength depends steeply on wavelength — a small change in length makes a huge change in how much light is bounced. Hence blue skies from short waves and red **sunsets** from long ones.",
      citations: 2,
    },
    eli5: {
      title: "Wavelength, simply",
      body: "Light is a wave. Short waves look blue, long waves look red — and short waves get bounced around much more by the air.",
      citations: 1,
    },
    example: {
      title: "Wavelengths in scale",
      body: "Radio waves can be metres long; visible light is around half a micrometre. They are the same kind of thing, just at wildly different lengths.",
      citations: 1,
    },
    define: {
      title: "Wavelength",
      body: "Wavelength — the distance between successive peaks of a wave. For light, it determines colour: short is blue, long is red.",
      citations: 1,
    },
  },
  violet: {
    dive: {
      title: "Why not violet?",
      body: "Violet has an even shorter wavelength than blue, so it scatters even more — the sky should look violet. It doesn't, for two reasons: our **eyes** are far more sensitive to blue, and the upper **atmosphere** soaks up some violet before it reaches us.",
      citations: 3,
    },
    eli5: {
      title: "Why the sky isn't violet",
      body: "Violet bounces around even more than blue — but your **eyes** barely notice violet, and the air soaks some of it up. So blue wins.",
      citations: 1,
    },
    define: {
      title: "Violet",
      body: "Violet — the shortest wavelength we can see, sitting just beyond blue at the edge of the rainbow.",
      citations: 1,
    },
  },
  eyes: {
    dive: {
      title: "Why our eyes prefer blue",
      body: "The human retina has three kinds of cone cell. Our blue-sensitive cones dominate how we read a sky that is really a mix of blue and violet — so a slightly violet sky simply looks blue to us.",
      citations: 2,
    },
    eli5: {
      title: "Your eyes",
      body: "Your eyes are wired to notice blue much more than violet — so that is the colour you end up seeing.",
      citations: 1,
    },
    define: {
      title: "Eyes",
      body: "Eyes — our light detectors. Cone cells inside them build colour vision from just three signals.",
      citations: 1,
    },
  },
  sun: {
    dive: {
      title: "The Sun's light",
      body: "The Sun emits a broad, roughly white spectrum, but less of its deep-violet light reaches the ground. That, plus how our **eyes** work, is another reason the sky settles on blue rather than violet.",
      citations: 2,
    },
    define: {
      title: "The Sun",
      body: "The Sun — our star. Its white light is a blend of every visible colour.",
      citations: 1,
    },
  },
  red: {
    dive: {
      title: "Red light",
      body: "Red has a long wavelength, so it scatters far less and mostly passes straight through the air. That is why the Sun itself looks reddish when it sits low near the **horizon**.",
      citations: 2,
    },
    eli5: {
      title: "Red light",
      body: "Red light mostly ignores the air and keeps going straight — which is why the Sun itself looks red near sundown.",
      citations: 1,
    },
    define: {
      title: "Red",
      body: "Red — the longest wavelength we can see, and the one the air scatters least.",
      citations: 1,
    },
  },
  sunsets: {
    dive: {
      title: "Why sunsets are red",
      body: "At sunset the Sun sits low, so its light travels through much more **atmosphere** than at noon. Almost all the blue is scattered away before the light reaches you, leaving the reds and oranges — and painting the high clouds pink.",
      citations: 3,
    },
    eli5: {
      title: "Sunsets, simply",
      body: "At sunset, sunlight takes a long, low path. The air scatters away nearly all the blue, so only red and orange reach your eyes.",
      citations: 1,
    },
    example: {
      title: "The sky on Mars",
      body: "Mars has a thin, dusty atmosphere, so its daytime sky is butterscotch and its sunsets glow blue — the reverse of Earth. Different air, different scattering.",
      citations: 2,
    },
    define: {
      title: "Sunsets",
      body: "Sunsets — the reddening of the sky when sunlight takes a long, low path through the atmosphere and loses its blue.",
      citations: 1,
    },
  },
  atmosphere: {
    dive: {
      title: "The atmosphere",
      body: "The atmosphere is a thin shell of gas held down by gravity — mostly **nitrogen** and **oxygen**. Its molecules are the scattering centres that make the sky blue and the horizon pale.",
      citations: 2,
    },
    define: {
      title: "Atmosphere",
      body: "Atmosphere — the layer of gases wrapped around a planet, held there by gravity.",
      citations: 1,
    },
  },
  horizon: {
    dive: {
      title: "The horizon",
      body: "Near the horizon, sunlight crosses more air, so more blue is scattered away — which is why the sky fades pale toward the horizon and why the setting Sun reddens.",
      citations: 2,
    },
    define: {
      title: "Horizon",
      body: "Horizon — the line where the sky appears to meet the ground, where we look through the most air.",
      citations: 1,
    },
  },
};

const KIND_LABELS = {
  root: "Answer",
  dive: "Dive in",
  eli5: "ELI5",
  example: "Examples",
  define: "Define",
  note: "Note",
};

function normalizeKey(text) {
  return String(text)
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function synthesize(anchor, kind, lens) {
  const a = anchor.trim();
  const low = a.toLowerCase();
  const styleHint =
    lens && lens.style === "analogy"
      ? " Think of it by analogy: it behaves like the moving part in a machine — nudge it and everything nearby responds."
      : lens && lens.style === "technical"
      ? " Formally: trace the cause, follow the effect, and the mechanism falls out of the relationships around it."
      : "";

  if (kind === "eli5") {
    return {
      title: `${a}, simply`,
      body: `Here is the simplest version of **${a}**: picture one moving part inside a bigger machine. When it changes, the pieces around it change too — and that is really all you need to hold onto for now.${styleHint}`,
      citations: 1,
    };
  }
  if (kind === "example") {
    return {
      title: `Examples of ${a}`,
      body: `Take **${a}** and drop it into a situation you already know. Once you spot the pattern there, you will start noticing it everywhere — the same shape wearing different clothes.`,
      citations: 1,
    };
  }
  if (kind === "define") {
    return {
      title: a,
      body: `**${a}** — a term worth keeping in your pocket. In one line: the idea that connects what came before it to what it causes.`,
      citations: 1,
    };
  }
  return {
    title: a,
    body: `Going a level deeper on **${a}**. The useful move is to stop treating it as a name and start asking what it does: what causes it, what it causes in turn, and where it sits relative to the ideas around it. Trace that and the detail stops feeling arbitrary.${styleHint}`,
    citations: 2,
  };
}

function styleSuffix(lens) {
  if (lens && lens.style === "analogy") return " Think of it by analogy: it behaves like the moving part in a machine — nudge it and everything nearby responds.";
  if (lens && lens.style === "technical") return " Formally: trace the cause, follow the effect, and the mechanism falls out of the relationships around it.";
  return "";
}

function generateRoot(question, lens) {
  const q = String(question).trim();
  if (normalizeKey(q) === normalizeKey(SEED_QUESTION)) {
    return {
      title: q,
      body: SEED_ROOT.body,
      citations: 3,
      estReadSeconds: estimateReadSeconds(SEED_ROOT.body),
    };
  }
  const body = `You asked: **${q}**. The short version is that it rests on a few moving parts. Pull on any phrase below and we will follow it down — the picture fills in as the pieces connect.${styleSuffix(lens)}`;
  return {
    title: q,
    body,
    citations: 2,
    estReadSeconds: estimateReadSeconds(body),
  };
}

function estimateReadSeconds(text) {
  const words = String(text).trim().split(/\s+/).filter(Boolean).length;
  return Math.max(20, Math.round((words / 200) * 60));
}

function generateNode(parent, anchor, kind, lens) {
  const key = normalizeKey(anchor);
  const entry = LIBRARY[key];
  let data;
  if (entry && entry[kind]) {
    data = entry[kind];
  } else if (entry && entry.dive) {
    data = entry.dive;
  } else {
    data = synthesize(anchor, kind, lens);
  }
  const suffix = kind === "dive" ? " · in depth" : "";
  return {
    title: data.title + (kind === "dive" && data.title === anchor.trim() ? suffix : ""),
    body: data.body,
    citations: data.citations || 1,
    estReadSeconds: estimateReadSeconds(data.body),
  };
}

window.SEED_QUESTION = SEED_QUESTION;
window.SEED_ROOT = SEED_ROOT;
window.KIND_LABELS = KIND_LABELS;
window.generateNode = generateNode;
window.generateRoot = generateRoot;
window.estimateReadSeconds = estimateReadSeconds;

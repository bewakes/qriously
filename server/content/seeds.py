DEFAULT_SEED_LENS = {
    "familiarity": "basics",
    "depth": "solid",
    "style": "plain",
    "goal": "curious",
}

SEED_VARIANTS = [
    {
        "text": "Why is the sky blue?",
        "kind": "root",
        "kind_hint": "question",
        "context_key": "",
        "lens": DEFAULT_SEED_LENS,
        "title": "Why is the sky blue?",
        "body": (
            "Sunlight looks white, but it is really every color mixed together. "
            "When it enters the atmosphere it meets countless tiny molecules of "
            "**nitrogen** and **oxygen**. These molecules bounce the shorter, "
            "bluer wavelengths around far more than the longer, redder ones. "
            "That scattered blue light reaches your eyes from every direction, "
            "so the whole sky glows blue.\n\n"
            "The effect is called **Rayleigh scattering**. It is why the sky "
            "reddens at sunset, when light travels through much more air."
        ),
    },
    {
        "text": "Rayleigh scattering",
        "kind": "dive",
        "kind_hint": "phrase",
        "context_key": "why is the sky blue",
        "lens": DEFAULT_SEED_LENS,
        "title": "Rayleigh scattering, in detail",
        "body": (
            "Rayleigh scattering is the elastic scattering of light by particles "
            "much smaller than its **wavelength**. The scattering intensity grows "
            "with the inverse fourth power of wavelength, so **blue light** is "
            "scattered roughly ten times more than red.\n\n"
            "Because the effect depends on the fourth power, small changes in "
            "wavelength produce large changes in how much light is redirected."
        ),
    },
    {
        "text": "Rayleigh scattering",
        "kind": "define",
        "kind_hint": "phrase",
        "context_key": "",
        "lens": DEFAULT_SEED_LENS,
        "title": "Rayleigh scattering",
        "body": (
            "**Rayleigh scattering** is the scattering of electromagnetic "
            "radiation by particles smaller than about one tenth of the "
            "radiation's **wavelength**."
        ),
    },
    {
        "text": "Why is the sky blue?",
        "kind": "eli5",
        "kind_hint": "question",
        "context_key": "",
        "lens": DEFAULT_SEED_LENS,
        "title": "The sky is blue, explained simply",
        "body": (
            "Imagine sunlight is a bag of colored balls. The tiny bits of air "
            "love the blue balls and toss them everywhere, like confetti. Red "
            "balls fly straighter and mostly miss the air bits. So blue "
            "confetti lands on your eyes from all over the sky."
        ),
    },
    {
        "text": "Rayleigh scattering",
        "kind": "example",
        "kind_hint": "phrase",
        "context_key": "why is the sky blue",
        "lens": DEFAULT_SEED_LENS,
        "title": "Rayleigh scattering in everyday life",
        "body": (
            "- A clear midday sky is **blue** — short wavelengths scatter "
            "overhead.\n"
            "- At **sunset**, light crosses more air and the blue scatters away, "
            "leaving reds and oranges.\n"
            "- Distant mountains look hazy and blue for the same reason."
        ),
    },
]

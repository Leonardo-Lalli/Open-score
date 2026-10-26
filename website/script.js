(() => {
  const THEME_KEY = "openScoreSiteTheme";
  const root = document.documentElement;

  // --- Navigation ---------------------------------------------------------
  const navToggle = document.getElementById("nav-toggle");
  const nav = document.getElementById("site-nav");
  let closeNav = () => {};

  if (navToggle && nav) {
    const setOpen = (open) => {
      nav.classList.toggle("open", open);
      navToggle.setAttribute("aria-expanded", String(open));
      navToggle.setAttribute(
        "aria-label",
        open ? "Chiudi il menu" : "Apri il menu",
      );
    };

    closeNav = () => setOpen(false);

    navToggle.addEventListener("click", () => {
      setOpen(!nav.classList.contains("open"));
    });

    nav.addEventListener("click", (event) => {
      if (event.target.closest("a")) setOpen(false);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setOpen(false);
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 820) setOpen(false);
    });
  }

  // --- Theme --------------------------------------------------------------
  const themeToggle = document.getElementById("theme-toggle");
  const themeMenu = document.getElementById("theme-menu");
  const themeRadios = [...document.querySelectorAll('input[name="site-theme"]')];
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  let menuOpen = false;
  let currentChoice = readChoice();

  function readChoice() {
    try {
      const stored = localStorage.getItem(THEME_KEY);
      return stored === "light" || stored === "dark" ? stored : "system";
    } catch {
      return "system";
    }
  }

  function resolved(choice) {
    if (choice !== "system") return choice;
    return media.matches ? "dark" : "light";
  }

  function updateMeta(theme) {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta)
      meta.setAttribute("content", theme === "dark" ? "#0f1a16" : "#f6f7f2");
  }

  function apply(choice, persist) {
    currentChoice = choice;
    const theme = resolved(choice);
    root.dataset.theme = theme;
    root.dataset.themeChoice = choice;
    root.style.colorScheme = theme;
    root.style.backgroundColor = theme === "dark" ? "#0f1a16" : "#f6f7f2";
    updateMeta(theme);

    if (themeToggle) {
      const labels = { light: "chiaro", dark: "scuro", system: "sistema" };
      const text = `Tema: ${labels[choice]}`;
      themeToggle.setAttribute("aria-label", text);
      themeToggle.setAttribute("title", text);
    }

    for (const radio of themeRadios) radio.checked = radio.value === choice;

    if (persist) {
      try {
        localStorage.setItem(THEME_KEY, choice);
      } catch {
        // Private mode or blocked storage: the theme still applies for this page.
      }
    }
  }

  function setMenu(open, focus = false) {
    if (!themeMenu || !themeToggle) return;
    menuOpen = open;
    themeMenu.hidden = !open;
    themeToggle.setAttribute("aria-expanded", String(open));
    if (open && focus) {
      const checked = themeRadios.find((radio) => radio.checked);
      (checked || themeRadios[0])?.focus();
    }
  }

  if (themeToggle && themeMenu) {
    themeToggle.addEventListener("click", () => {
      closeNav();
      setMenu(!menuOpen, true);
    });

    themeMenu.addEventListener("change", (event) => {
      const radio = event.target.closest('input[name="site-theme"]');
      if (!radio) return;
      apply(radio.value, true);
      setMenu(false);
      themeToggle.focus();
    });

    document.addEventListener("click", (event) => {
      if (!menuOpen) return;
      if (
        themeToggle.contains(event.target) ||
        themeMenu.contains(event.target)
      )
        return;
      setMenu(false);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape" || !menuOpen) return;
      setMenu(false);
      themeToggle.focus();
    });
  }

  const onSystemChange = () => {
    if (currentChoice === "system") apply("system", false);
  };
  if (typeof media.addEventListener === "function")
    media.addEventListener("change", onSystemChange);
  else if (typeof media.addListener === "function")
    media.addListener(onSystemChange);

  apply(currentChoice, false);

  // --- Footer year --------------------------------------------------------
  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
})();

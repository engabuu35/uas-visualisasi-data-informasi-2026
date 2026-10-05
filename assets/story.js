// Halaman Cerita: latar yang bergeser per babak, animasi sekali-masuk,
// tooltip, crosshair, dan penanda babak. Tanpa pustaka.
(() => {
  const root = document.querySelector(".ws");
  if (!root || root.dataset.ready) return;   // Streamlit bisa menjalankan ulang skrip
  root.dataset.ready = "1";

  // SVG tiba sebagai data karena sanitizer membuang svg; jangan tulis tag di file ini.
  const svgs = window.__WS_SVG || {};
  root.querySelectorAll("[data-slot]").forEach((el) => { el.innerHTML = svgs[el.dataset.slot] || ""; });

  // Tanpa gerak bila sistem operasi memintanya ATAU pengguna memilih "Hentikan animasi".
  const reduce = window.__WS_STILL === true || matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Yang menggulir adalah wadah utama Streamlit, bukan window.
  const scroller = document.querySelector('[data-testid="stMain"]') || window;
  const acts = [...root.querySelectorAll(".ws-act")];
  const scenes = [...root.querySelectorAll(".ws-cards")].map((w) => [...w.querySelectorAll(".ws-card")]);
  // Kartu pertama dan terakhir tiap adegan sejajar tengah grafik (desktop). Ruang bawah
  // membuat grafik tetap tersemat sampai kartu terakhir sampai di tengah, baru ikut terangkat.
  const narrow = matchMedia("(max-width: 820px)");
  const centerFirst = () => root.querySelectorAll(".ws-scene").forEach((sc) => {
    const cards = sc.querySelector(".ws-cards"), stage = sc.querySelector(".ws-stage");
    const all = cards ? cards.querySelectorAll(".ws-card") : [];
    if (!all.length || !stage) return;
    // Grafik tersemat di tengah layar; bila lebih tinggi dari layar, ia menempel di bawah header.
    // data-nudge: geser grafik adegan tertentu sedikit ke bawah (px), tanpa melewati tepi bawah layar.
    const h = stage.offsetHeight, base = Math.max(76, (innerHeight - h) / 2);
    const top = Math.max(base, Math.min(base + (+sc.dataset.nudge || 0), innerHeight - h - 16));
    stage.style.top = narrow.matches ? "" : `${top}px`;
    // Ruang atas: kartu pertama sejajar tengah grafik. Ruang bawah: grafik tetap tersemat sampai kartu
    // terakhir tepat di tengah layar (bawah adegan = bawah grafik tersemat), baru keduanya terangkat.
    const first = all[0], last = all[all.length - 1];
    cards.style.paddingTop = narrow.matches ? "" : `${Math.max(0, (h - first.offsetHeight) / 2)}px`;
    cards.style.paddingBottom = narrow.matches ? ""
      : `${Math.max(0, top + h - (innerHeight / 2 + last.offsetHeight / 2))}px`;
  });
  centerFirst();
  // Tinggi grafik/kartu bisa berubah setelah dihitung (font, bungkus baris, SVG): hitung ulang saat itu.
  if ("ResizeObserver" in window) {
    const ro = new ResizeObserver(centerFirst);
    root.querySelectorAll(".ws-stage, .ws-card").forEach((el) => ro.observe(el));
  }
  addEventListener("resize", centerFirst, { passive: true });
  addEventListener("load", centerFirst);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(centerFirst);
  const rail = [...root.querySelectorAll(".ws-rail button")];
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  // Tint dibaca langsung dari variabel CSS agar latar ikut tema aktif.
  let tints = [];
  const readTints = () => { tints = acts.map((a) => hex(getComputedStyle(a).getPropertyValue("--tint").trim())); };
  readTints();

  // ---- Latar mengikuti babak ------------------------------------------------
  // Warna hanya beralih di sekitar batas babak (±30% tinggi layar).
  let ticking = false;
  function paint() {
    ticking = false;
    const vh = innerHeight, mid = vh / 2;
    let c = tints[0], active = 0;
    for (let i = 1; i < acts.length; i++) {
      const b = acts[i].getBoundingClientRect().top;
      const t = Math.min(1, Math.max(0, (mid - (b - 0.3 * vh)) / (0.6 * vh)));
      if (t > 0) c = tints[i - 1].map((v, j) => Math.round(v + (tints[i][j] - v) * t));
      if (b < mid) active = i;
    }
    if (!reduce) root.style.setProperty("--ws-bg", `rgb(${c.join(",")})`);
    // Kartu aktif per adegan = kartu yang pusatnya paling dekat ke tengah layar.
    scenes.forEach((cards) => {
      let best = null, bd = Infinity;
      cards.forEach((c) => {
        const r = c.getBoundingClientRect(), d = Math.abs(r.top + r.height / 2 - mid);
        if (d < bd) { bd = d; best = c; }
      });
      cards.forEach((c) => c.classList.toggle("is-dim", c !== best));
    });
    rail.forEach((btn, i) => (i === active ? btn.setAttribute("aria-current", "step") : btn.removeAttribute("aria-current")));
  }
  const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(paint); } };
  scroller.addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll, { passive: true });
  paint();
  new MutationObserver(() => { readTints(); paint(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ["data-st-theme"] });

  rail.forEach((btn, i) => btn.addEventListener("click", () =>
    acts[i].scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" })));

  // ---- Masuk layar: animasi sekali saja --------------------------------------
  const count = (el) => {
    const to = +el.dataset.to, t0 = performance.now(), dur = 900;
    const step = (now) => {
      const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(to * e);   // langsung ke DOM, tanpa render ulang
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  if (reduce) {
    root.classList.add("ws-static");
    root.querySelectorAll(".ws-chart").forEach((c) => c.classList.add("is-in"));
  } else {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (!en.isIntersecting) return;
      en.target.classList.add("is-in");
      en.target.querySelectorAll(".ws-count").forEach(count);
      io.unobserve(en.target);
    }), { threshold: 0.3 });
    root.querySelectorAll(".ws-chart").forEach((c) => io.observe(c));
  }

  // ---- Tooltip ---------------------------------------------------------------
  const tip = document.createElement("div");
  tip.className = "ws-tip"; tip.setAttribute("role", "status");
  root.appendChild(tip);
  const place = (x, y) => {
    const r = tip.getBoundingClientRect();
    let left = x + 14, top = y + 14;
    if (left + r.width > innerWidth - 8) left = x - r.width - 14;
    if (top + r.height > innerHeight - 8) top = y - r.height - 14;
    tip.style.left = `${Math.max(8, left)}px`; tip.style.top = `${Math.max(8, top)}px`;
  };
  const show = (text, x, y) => { tip.textContent = text; tip.classList.add("on"); place(x, y); };
  const hide = () => tip.classList.remove("on");
  root.addEventListener("pointermove", (e) => {
    const t = e.target.closest && e.target.closest("[data-tip]");
    if (t && root.contains(t)) show(t.getAttribute("data-tip"), e.clientX, e.clientY);
    else if (!e.target.closest(".ws-xhair")) hide();
  });
  root.addEventListener("pointerleave", hide);
  root.addEventListener("focusin", (e) => {
    const t = e.target.closest("[data-tip]");
    if (!t) return;
    const r = t.getBoundingClientRect();
    show(t.getAttribute("data-tip"), r.left + r.width / 2, r.top);
  });
  root.addEventListener("focusout", hide);
  scroller.addEventListener("scroll", hide, { passive: true });

  // ---- Crosshair kurva konsentrasi ------------------------------------------
  root.querySelectorAll(".ws-xhair").forEach((svg) => {
    const ys = svg.dataset.ys.split(",").map(Number), names = svg.dataset.names.split("|");
    const x0 = +svg.dataset.x0, x1 = +svg.dataset.x1, y0 = +svg.dataset.y0, y1 = +svg.dataset.y1;
    const n = ys.length, line = svg.querySelector(".ws-xh-line"), dot = svg.querySelector(".ws-xh-dot");
    const hit = svg.querySelector(".ws-xh-hit"), pt = svg.createSVGPoint();
    const fmt = (v) => v.toFixed(1).replace(".", ",");
    hit.addEventListener("pointermove", (e) => {
      pt.x = e.clientX; pt.y = e.clientY;
      const p = pt.matrixTransform(svg.getScreenCTM().inverse());
      const i = Math.min(n, Math.max(1, Math.round(((p.x - x0) / (x1 - x0)) * n)));
      const x = x0 + (i / n) * (x1 - x0), y = y0 + (1 - ys[i - 1] / 100) * (y1 - y0);
      line.setAttribute("x1", x); line.setAttribute("x2", x);
      dot.setAttribute("cx", x); dot.setAttribute("cy", y);
      svg.classList.add("is-hover");
      show(`${i} daerah teratas\nmenghasilkan ${fmt(ys[i - 1])}% PDRB\nke-${i}: ${names[i - 1]}`, e.clientX, e.clientY);
    });
    hit.addEventListener("pointerleave", () => { svg.classList.remove("is-hover"); hide(); });
  });
})();

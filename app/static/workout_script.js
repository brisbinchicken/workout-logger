(() => {
  const form = document.getElementById("workout-form");
  if (!form) return;
  const KEY = "workout_autosave_v1";
  let SKIP = false;
  const q = n => form.elements[n];

  function save() {
    if (SKIP) return;
    const fd = new FormData(form);
    localStorage.setItem(KEY, JSON.stringify(Object.fromEntries(fd.entries())));
  }

  function load() {
    const raw = localStorage.getItem(KEY);
    if (!raw) return;
    try {
      const obj = JSON.parse(raw);
      for (const [k, v] of Object.entries(obj)) {
        if (q(k)) q(k).value = v;
      }
    } catch (e) {}
  }

  function setTodayAndNow() {
    const d = new Date();
    const pad = n => String(n).padStart(2, "0");
    const yyyy = d.getFullYear();
    const mm = pad(d.getMonth() + 1);
    const dd = pad(d.getDate());
    const hh = pad(d.getHours());
    const mi = pad(d.getMinutes());
    if (q("date")) q("date").value = `${yyyy}-${mm}-${dd}`;
    if (q("time")) q("time").value = `${hh}:${mi}`;
  }

  // Live clock: update the time field every 10 seconds
  setInterval(setTodayAndNow, 10000);

  document.addEventListener("DOMContentLoaded", () => {
    if (sessionStorage.getItem("justSubmitted") === "1") {
      sessionStorage.removeItem("justSubmitted");
      form.reset();
    } else {
      load();
    }
    setTodayAndNow();
    const ex = q("exercise");
    if (ex) ex.value = ""; // reset to blank placeholder
  });

  form.addEventListener("input", save);
  window.addEventListener("beforeunload", () => { if (!SKIP) save(); });

  form.addEventListener("submit", () => {
    SKIP = true;
    localStorage.removeItem(KEY);
    sessionStorage.setItem("justSubmitted", "1");

    // Clear instantly without waiting for page reload
    setTimeout(() => {
      form.reset();
      setTodayAndNow(); // force fresh time
      const ex = q("exercise");
      if (ex) ex.value = ""; // reset dropdown
    }, 50);
  });

  const finishForm = document.getElementById("finish-form");
  if (finishForm) finishForm.addEventListener("submit", () => {
    SKIP = true;
    localStorage.removeItem(KEY);
    sessionStorage.setItem("justSubmitted", "1");
  });
})();

const $ = (id) => document.getElementById(id);
const LANG_COLORS = { Python:"#3572A5", JavaScript:"#f1e05a", TypeScript:"#3178c6", Java:"#b07219", "C++":"#f34b7d",
  C:"#555555", "C#":"#178600", Go:"#00ADD8", Rust:"#dea584", HTML:"#e34c26", CSS:"#563d7c", Shell:"#89e051",
  "Jupyter Notebook":"#DA5B0B", Ruby:"#701516", PHP:"#4F5D95", Kotlin:"#A97BFF", Swift:"#F05138", Dart:"#00B4AB", Other:"#8b949e" };
const color = (l) => LANG_COLORS[l] || "#" + ((Math.abs([...l].reduce((a, c) => a * 31 + c.charCodeAt(0), 7)) % 0xffffff).toString(16).padStart(6, "0"));
let state = { user: null, pie: null };

function toast(msg) { const t = $("error"); t.textContent = msg; t.classList.remove("hidden"); setTimeout(() => t.classList.add("hidden"), 4000); }
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function load(user, refresh = false) {
  state.user = user;
  history.replaceState(null, "", `?user=${encodeURIComponent(user)}`);
  $("empty").textContent = "Loading…";
  try {
    const profile = await API.profile(user, refresh);   // also warms repo cache
    const [contrib, repos] = await Promise.all([API.contributions(user, refresh), API.repos(user, $("sort").value)]);
    renderProfile(profile, contrib);
    renderHeatmap(contrib);
    renderRepos(repos);
    $("app").classList.remove("hidden"); $("empty").classList.add("hidden"); $("chat-toggle").classList.remove("hidden");
    const settings = await API.settings(user);
    if (settings.last_job_description) { $("jd").value = settings.last_job_description; runMatch(); } else { $("match-badge").classList.add("hidden"); $("match-result").innerHTML = ""; }
    loadInsights();
  } catch (e) { $("empty").textContent = "Enter a GitHub username to build a portfolio."; toast(e.message); }
}

function renderProfile(p, c) {
  $("avatar").src = p.avatar_url; $("name").textContent = p.name;
  $("login").textContent = "@" + p.login; $("login").href = p.html_url;
  $("bio").textContent = [p.bio, p.location].filter(Boolean).join(" · ");
  $("followers").textContent = p.followers; $("stars").textContent = p.total_stars;
  $("forks").textContent = p.total_forks; $("repo-count").textContent = p.repo_count;
  $("streak").textContent = c.streaks.current + "d"; $("longest").textContent = c.streaks.longest + "d";
  if (state.pie) state.pie.destroy();
  state.pie = new Chart($("lang-pie"), {
    type: "pie",
    data: { labels: p.top_languages.map((l) => l.language),
      datasets: [{ data: p.top_languages.map((l) => l.percent), backgroundColor: p.top_languages.map((l) => color(l.language)), borderColor: "#161b22" }] },
    options: { plugins: { legend: { position: "right", labels: { color: "#e6edf3", boxWidth: 10, font: { size: 11 } } },
      tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.raw}%` } } } },
  });
}

function renderHeatmap(c) {
  const el = $("heatmap"); el.innerHTML = "";
  const first = new Date(c.days[0].date + "T00:00:00");
  for (let i = 0; i < first.getDay(); i++) el.appendChild(document.createElement("span")); // align weekday rows
  for (const d of c.days) {
    const cell = document.createElement("i");
    cell.className = "l" + d.level; cell.title = `${d.count} contributions on ${d.date}`;
    el.appendChild(cell);
  }
  $("contrib-meta").textContent = `${c.total} contributions · source: ${c.source === "graphql" ? "GraphQL calendar" : "public events (add token for full year)"}`;
}

function renderRepos(repos) {
  $("repos").innerHTML = repos.map((r) => `
    <div class="repo">
      <a href="${esc(r.url)}" target="_blank">${esc(r.name)}</a>
      <p>${esc(r.description) || "<i>No description</i>"}</p>
      <div class="meta">
        ${r.language ? `<span><span class="dot" style="background:${color(r.language)}"></span>${esc(r.language)}</span>` : ""}
        <span>★ ${r.stars}</span><span>⑂ ${r.forks}</span>
      </div>
    </div>`).join("") || "<p>No public repositories.</p>";
}

async function runMatch() {
  const jd = $("jd").value.trim();
  if (jd.length < 10) return toast("Job description is too short.");
  try {
    const m = await API.match(state.user, jd);
    const badge = $("match-badge");
    badge.textContent = `🎯 ${m.match_percentage}% Tech Stack Match · ${m.badge.label}`;
    badge.style.background = m.badge.color; badge.classList.remove("hidden");
    $("match-result").innerHTML = m.message ? `<p>${esc(m.message)}</p>` : `
      <p><b>${m.matched.length}/${m.required.length}</b> required skills found</p>
      <div class="chips">${m.matched.map((s) => `<span class="chip ${s.via === "direct" ? "ok" : "partial"}" title="${s.via}">${esc(s.skill)}${s.strength ? " · " + s.strength + "%" : ""}</span>`).join("")}</div>
      <div class="chips">${m.missing.map((s) => `<span class="chip miss">${esc(s)}</span>`).join("")}</div>`;
    loadInsights();
  } catch (e) { toast(e.message); }
}

async function loadInsights() {
  try {
    const i = await API.insights(state.user);
    $("ai-bio").textContent = i.bio;
    const s = i.portfolio_strength;
    $("strength").innerHTML = `<p><b>Portfolio strength: ${s.score}/100</b></p><div class="meter"><div style="width:${s.score}%"></div></div>
      <ul>${s.tips.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>`;
    $("roadmap").innerHTML = i.skill_gap_roadmap.length ? `<p><b>Skill-gap roadmap</b> (from last job match)</p><ul>${i.skill_gap_roadmap
      .map((r) => `<li><b>${esc(r.skill)}</b>: ${esc(r.starter_project)}${r.resource ? ` — <a href="${esc(r.resource)}" target="_blank">learn</a>` : ""}</li>`).join("")}</ul>` : "";
  } catch (e) { /* non-critical */ }
}

function addMsg(text, who) { const d = document.createElement("div"); d.className = "msg " + who; d.textContent = text; $("chat-log").appendChild(d); $("chat-log").scrollTop = 1e9; }

$("search-form").onsubmit = (e) => { e.preventDefault(); load($("username").value.trim()); };
$("refresh").onclick = () => state.user && load(state.user, true);
$("sort").onchange = async () => renderRepos(await API.repos(state.user, $("sort").value));
$("match-btn").onclick = runMatch;
$("chat-toggle").onclick = () => { $("chat").classList.remove("hidden"); $("chat-toggle").classList.add("hidden");
  if (!$("chat-log").children.length) addMsg("Hi! Ask me about top projects, languages, streaks, or skills.", "bot"); };
$("chat-close").onclick = () => { $("chat").classList.add("hidden"); $("chat-toggle").classList.remove("hidden"); };
$("chat-form").onsubmit = async (e) => {
  e.preventDefault(); const m = $("chat-input").value.trim(); if (!m) return;
  addMsg(m, "user"); $("chat-input").value = "";
  try { addMsg((await API.chat(state.user, m)).reply, "bot"); } catch (err) { addMsg("Error: " + err.message, "bot"); }
};
const q = new URLSearchParams(location.search).get("user");
if (q) { $("username").value = q; load(q); }

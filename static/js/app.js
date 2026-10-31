const $ = (selector) => document.querySelector(selector);

async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

async function loadDashboard() {
  const list = $("#problem-list");
  if (!list) return;
  const search = $("#search"), topic = $("#topic-filter"), difficulty = $("#difficulty-filter");
  let allProblems = [];
  try {
    allProblems = await requestJSON("/api/problems");
    const topics = [...new Set(allProblems.map(p => p.topic))].sort();
    topics.forEach(name => {
      const option = document.createElement("option");
      option.value = name; option.textContent = name; topic.appendChild(option);
    });
    const render = () => {
      const q = search.value.toLowerCase();
      const filtered = allProblems.filter(p =>
        (!q || `${p.title} ${p.description} ${p.topic}`.toLowerCase().includes(q)) &&
        (!topic.value || p.topic === topic.value) &&
        (!difficulty.value || p.difficulty === difficulty.value)
      );
      $("#problem-count").textContent = `${filtered.length} problems`;
      list.innerHTML = "";
      if (!filtered.length) {
        list.innerHTML = '<div class="loading">No problems match these filters.</div>';
        return;
      }
      filtered.forEach(p => {
        const a = document.createElement("a");
        a.className = "problem-card"; a.href = `/problem/${p.id}`;
        const top = document.createElement("div"); top.className = "card-top";
        const tag = document.createElement("span"); tag.className = "tag"; tag.textContent = p.topic;
        const level = document.createElement("span"); level.className = `difficulty ${p.difficulty.toLowerCase()}`; level.textContent = p.difficulty;
        top.append(tag, level);
        const title = document.createElement("h3"); title.textContent = p.title;
        const desc = document.createElement("p"); desc.textContent = p.description;
        a.append(top, title, desc); list.appendChild(a);
      });
    };
    [search, topic, difficulty].forEach(el => el.addEventListener("input", render));
    render();
  } catch (error) { list.textContent = error.message; }
}

async function loadHistory(problemId) {
  const target = $("#history-list");
  if (!target) return;
  try {
    const items = await requestJSON(`/api/submissions/${problemId}`);
    target.innerHTML = "";
    if (!items.length) { target.textContent = "No submissions yet."; return; }
    items.forEach(item => {
      const row = document.createElement("div"); row.className = "history-item";
      const left = document.createElement("span"); left.textContent = `${item.created_at} · ${item.passed}/${item.total} tests`;
      const right = document.createElement("strong"); right.textContent = item.status;
      right.className = item.status === "Accepted" ? "accepted" : "rejected";
      row.append(left, right); target.appendChild(row);
    });
  } catch (error) { target.textContent = error.message; }
}

function showRunResult(data, isSubmission) {
  const target = $("#run-output");
  target.innerHTML = "";
  if (data.error) { target.textContent = data.error; return; }
  if (!isSubmission) {
    const heading = document.createElement("div"); heading.className = "result-heading";
    heading.textContent = data.status;
    const time = document.createElement("span"); time.textContent = `${data.runtime_ms} ms`; heading.append(time);
    target.append(heading);
    const output = document.createElement("pre"); output.textContent = data.stdout || "(no output)";
    target.append(output);
    if (data.stderr) { const err = document.createElement("pre"); err.className = "error"; err.textContent = data.stderr; target.append(err); }
    return;
  }
  const heading = document.createElement("div"); heading.className = "result-heading";
  const status = document.createElement("strong"); status.textContent = data.status; status.className = data.status === "Accepted" ? "accepted" : "rejected";
  const summary = document.createElement("span"); summary.textContent = `${data.passed}/${data.total} passed · ${data.runtime_ms} ms`;
  heading.append(status, summary); target.append(heading);
  data.results.forEach(item => {
    const row = document.createElement("div"); row.className = "test-row";
    const line = document.createElement("strong");
    const name = document.createElement("span"); name.textContent = `Test case ${item.case}`;
    const result = document.createElement("span"); result.textContent = item.status; result.className = item.passed ? "accepted" : "rejected";
    line.append(name, result); row.append(line);
    if (item.input !== undefined) {
      const details = document.createElement("details");
      const summary = document.createElement("summary"); summary.textContent = "View case details";
      details.append(summary);
      [["Input", item.input], ["Expected", item.expected], ["Actual", item.actual], ["Error", item.stderr]].forEach(([label, value]) => {
        if (!value) return;
        const title = document.createElement("div"); title.textContent = label;
        const pre = document.createElement("pre"); pre.textContent = value;
        details.append(title, pre);
      });
      row.append(details);
    } else {
      const note = document.createElement("div"); note.textContent = "Hidden test case"; note.className = "muted";
      row.append(note);
    }
    target.append(row);
  });
  loadHistory(window.ALGO_PROBLEM.id);
  refreshStats();
}

async function refreshStats() {
  try {
    const stats = await requestJSON("/api/stats");
    if ($("#stat-problems")) $("#stat-problems").textContent = stats.total_problems;
    if ($("#stat-solved")) $("#stat-solved").textContent = stats.solved_problems;
    if ($("#stat-submissions")) $("#stat-submissions").textContent = stats.total_submissions;
    if ($("#stat-rate")) $("#stat-rate").textContent = `${stats.success_rate}%`;
  } catch (_) {}
}

function initProblemPage() {
  if (!window.ALGO_PROBLEM) return;
  const editor = $("#code-editor"), output = $("#run-output");
  $("#reset-code").addEventListener("click", () => { editor.value = window.ALGO_PROBLEM.starterCode; });
  async function execute(endpoint, payload, submission) {
    const button = submission ? $("#submit-button") : $("#run-button");
    button.disabled = true; button.textContent = "Running...";
    output.innerHTML = '<div class="empty-state">Executing your solution...</div>';
    try {
      const data = await requestJSON(endpoint, { method: "POST", body: JSON.stringify(payload) });
      showRunResult(data, submission);
    } catch (error) { output.textContent = error.message; }
    finally {
      button.disabled = false;
      button.textContent = submission ? "Submit solution" : "▶ Run custom input";
    }
  }
  $("#run-button").addEventListener("click", () => execute("/api/run", {
    code: editor.value, stdin: $("#custom-input").value
  }, false));
  $("#submit-button").addEventListener("click", () => execute("/api/submit", {
    code: editor.value, problem_id: window.ALGO_PROBLEM.id
  }, true));
  loadHistory(window.ALGO_PROBLEM.id);
}

document.addEventListener("DOMContentLoaded", () => { loadDashboard(); initProblemPage(); });

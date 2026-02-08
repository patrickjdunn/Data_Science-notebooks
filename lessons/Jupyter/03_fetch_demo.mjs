
// 03_fetch_demo.mjs
const url = "https://api.github.com/repos/nodejs/node";
const res = await fetch(url, { headers: { "User-Agent": "codespaces-demo" } });
if (!res.ok) throw new Error(`HTTP ${res.status}`);
const data = await res.json();
console.log({ full_name: data.full_name, stars: data.stargazers_count, updated_at: data.updated_at });

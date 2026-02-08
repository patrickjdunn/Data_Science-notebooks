
// bp_report.mjs
import fs from "fs";
import Papa from "papaparse";

const filename = process.argv[2];
if (!filename) {
  console.error("Usage: node bp_report.mjs <file.csv>");
  process.exit(1);
}

const text = fs.readFileSync(filename, "utf8");
const parsed = Papa.parse(text, { header: true, dynamicTyping: true });
const rows = parsed.data.filter(r => r.id != null);

const mean = (arr) => arr.reduce((a,b)=>a+b,0)/arr.length;

const sbps = rows.map(r => r.sbp).filter(x => Number.isFinite(x));
const dbps = rows.map(r => r.dbp).filter(x => Number.isFinite(x));

const report = {
  file: filename,
  n: rows.length,
  mean_sbp: sbps.length ? mean(sbps) : null,
  mean_dbp: dbps.length ? mean(dbps) : null,
  high_sbp_count: sbps.filter(x => x >= 140).length,
};

fs.writeFileSync("report.json", JSON.stringify(report, null, 2));
console.log("Wrote report.json");
console.log(report);

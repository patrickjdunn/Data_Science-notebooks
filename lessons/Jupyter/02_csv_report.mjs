
// 02_csv_report.mjs
import fs from "fs";
import Papa from "papaparse";

const text = fs.readFileSync("bp_sample.csv", "utf8");
const parsed = Papa.parse(text, { header: true, dynamicTyping: true });

const rows = parsed.data.filter(r => r.id != null);

const mean = (arr) => arr.reduce((a,b)=>a+b,0)/arr.length;

const sbps = rows.map(r => r.sbp);
const dbps = rows.map(r => r.dbp);

const report = {
  n: rows.length,
  mean_sbp: mean(sbps),
  mean_dbp: mean(dbps),
  high_sbp_count: sbps.filter(x => x >= 140).length,
};

function labelBP(sbp, dbp){
  if (sbp >= 140 || dbp >= 90) return "High (example)";
  if (sbp >= 130 || dbp >= 80) return "Elevated (example)";
  return "Normal (example)";
}

const labeled = rows.map(r => ({...r, label: labelBP(r.sbp, r.dbp)}));

console.log("Report:", report);
console.log("Labeled rows:");
console.table(labeled);

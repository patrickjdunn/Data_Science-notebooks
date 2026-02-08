
// 01_basics.mjs
const readings = [120, 135, 128, 142, 118];

const mean = arr => arr.reduce((a,b)=>a+b,0)/arr.length;

const summary = {
  n: readings.length,
  min: Math.min(...readings),
  max: Math.max(...readings),
  mean: mean(readings),
  highCount: readings.filter(x => x >= 140).length
};

console.log("BP Summary:", summary);

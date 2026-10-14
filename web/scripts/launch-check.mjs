// Launch check: fails while any visitor-facing TODO, em dash or contact placeholder remains in the
// website's text files (design rules). Run before launch with: npm run check:launch
import { readdirSync, readFileSync } from "node:fs";

const dir = new URL("../src/content/", import.meta.url);
const problems = [];

for (const name of readdirSync(dir)) {
  const lines = readFileSync(new URL(name, dir), "utf8").split(/\r?\n/);
  lines.forEach((line, index) => {
    const where = `src/content/${name}, line ${index + 1}`;
    if (line.includes("TODO (Anshul)")) problems.push(`${where}: text still to write`);
    if (line.includes("\u2014")) problems.push(`${where}: em dash`);
    if (/\[your /i.test(line)) problems.push(`${where}: placeholder still to fill in`);
  });
}

if (problems.length > 0) {
  console.log(`Not ready to launch: ${problems.length} item(s) left.\n`);
  for (const problem of problems) console.log(`  ${problem}`);
  process.exit(1);
}
console.log("Ready to launch: no TODOs, em dashes or placeholders left in the website text.");
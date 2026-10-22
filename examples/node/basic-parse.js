/**
 * Astars Rust core - usage example (Node binding).
 *
 * Prerequisites (one-time build step, from bindings/node/):
 *   npm install
 *   npm run build:debug
 *
 * Then run this file from the repo root:
 *   node examples/node/basic-parse.js
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { parseStr, parseBytes, parseFile, JsLang } = require('../../bindings/node/index.js');

const SOURCE = `def greet(name):
    return f"Hello, {name}!"


class Greeter:
    def __init__(self, name):
        self.name = name
`;

function main() {
  const tree = parseStr(SOURCE, JsLang.Python);
  console.log(`parsed ${tree.walk().length} nodes`);

  console.log('\nfunctions:');
  for (const id of tree.find('function_definition')) {
    const [start, end] = tree.spanOf(id);
    console.log(`  [${start}:${end}] ${JSON.stringify(tree.sourceOf(id))}`);
  }

  console.log('\nclasses:');
  for (const id of tree.find('class_definition')) {
    const info = tree.nodeInfo(id);
    console.log(`  ${info.kind} spans bytes ${info.startByte}-${info.endByte}, ` +
      `${info.children.length} direct children`);
  }

  const offset = SOURCE.indexOf('Greeter');
  const hit = tree.nodeAt(offset);
  console.log(`\nnode at offset ${offset} (inside 'Greeter'): ${tree.nodeInfo(hit).kind}`);

  const firstFunc = tree.find('function_definition')[0];
  const subtree = tree.dump(firstFunc);
  console.log(`\ndump() of the first function: ${subtree.length} nodes in one call`);

  console.log('\npointAt (0-based line/column for a byte offset):');
  const [line, column] = tree.pointAt(offset);
  console.log(`  offset ${offset} ('Greeter') is at line ${line}, column ${column}`);

  console.log('\nedit primitive (replace + unchangedIn):');
  const edit = tree.replace(firstFunc, 'def greet(name):\n    return f"Hi, {name}!"\n');
  const classDef = tree.find('class_definition')[0];
  console.log(`  replaced greet() - new tree has ${edit.tree.walk().length} nodes`);
  console.log(`  unchangedIn(class Greeter): ${tree.unchangedIn(classDef, edit)}`);
  console.log(`  unchangedIn(greet, the node we replaced): ${tree.unchangedIn(firstFunc, edit)}`);

  console.log('\nparseBytes (same source as a raw Buffer, not a string):');
  const bytesTree = parseBytes(Buffer.from(SOURCE, 'utf-8'), JsLang.Python);
  console.log(`  parsed ${bytesTree.walk().length} nodes (matches parseStr: ` +
    `${bytesTree.walk().length === tree.walk().length})`);

  console.log('\nparseFile (writing SOURCE to a temp file first):');
  const tmpPath = path.join(os.tmpdir(), `astars-basic-parse-example-${process.pid}.py`);
  fs.writeFileSync(tmpPath, SOURCE);
  try {
    const fileTree = parseFile(tmpPath, JsLang.Python);
    console.log(`  parsed ${fileTree.walk().length} nodes from ${tmpPath}`);
  } finally {
    fs.unlinkSync(tmpPath);
  }

  console.log('\ndiagnostics (parsing a source with a syntax error):');
  const broken = parseStr('def broken(:\n    pass\n', JsLang.Python);
  for (const diag of broken.diagnostics()) {
    console.log(`  [${diag.severity}] ${diag.message} at bytes ${diag.span}`);
  }
}

main();

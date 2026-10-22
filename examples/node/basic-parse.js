/**
 * Astars Rust core - minimal usage example (Node binding).
 *
 * Prerequisites (one-time build step, from bindings/node/):
 *   npm install
 *   npm run build:debug
 *
 * Then run this file from the repo root:
 *   node examples/node/basic-parse.js
 */

const { parseStr, JsLang } = require('../../bindings/node/index.js');

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
}

main();

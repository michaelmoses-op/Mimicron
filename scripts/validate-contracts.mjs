#!/usr/bin/env node
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import yaml from "js-yaml";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const contracts = join(root, "contracts");

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function loadDoc(path) {
  const raw = readFileSync(path, "utf8");
  if (path.endsWith(".yaml") || path.endsWith(".yml")) {
    return yaml.load(raw);
  }
  return JSON.parse(raw);
}

function validateOpenAPI(path) {
  const doc = loadDoc(path);
  if (!doc.openapi || !doc.info?.title) {
    throw new Error(`${path}: missing openapi or info.title`);
  }
  if (!doc.paths || Object.keys(doc.paths).length === 0) {
    throw new Error(`${path}: no paths defined`);
  }
  console.log(`OK OpenAPI ${path}`);
}

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);

const scenarioSchema = readJson(join(contracts, "scenario/scenario.schema.json"));
const envelopeSchema = readJson(join(contracts, "events/envelope.schema.json"));

ajv.compile(scenarioSchema);
ajv.compile(envelopeSchema);
console.log("OK JSON Schema scenario.schema.json");
console.log("OK JSON Schema envelope.schema.json");

const exampleYaml = readFileSync(
  join(root, "scenarios/examples/smart-building-heatwave.yaml"),
  "utf8",
);
const scenarioDoc = yaml.load(exampleYaml);
const validateScenario = ajv.compile(scenarioSchema);
if (!validateScenario(scenarioDoc)) {
  console.error(validateScenario.errors);
  process.exit(1);
}
console.log("OK example scenario validates against scenario.schema.json");

validateOpenAPI(join(contracts, "openapi/control-api.yaml"));
validateOpenAPI(join(contracts, "openapi/data-plane.yaml"));

for (const f of readdirSync(join(contracts, "events"))) {
  if (f.endsWith(".json")) {
    readJson(join(contracts, "events", f));
  }
}
console.log("Contracts validation passed.");

import assert from "node:assert/strict";
import test from "node:test";
import { trustEdits } from "../scripts/trust-codex-rtk.mjs";

const home = "/tmp/home with spaces/.codex";
const hook = {
  key: `${home}/hooks.json:pre_tool_use:0:0`, source: "user",
  command: "rtk hook codex", trustStatus: "untrusted",
  currentHash: "sha256:" + "a".repeat(64),
};

test("approve the exact global RTK hook and preserve content hashes", () => {
  const contentHash = "sha256:" + "b".repeat(64);
  const [edit] = trustEdits([{ ...hook, currentHash: hook.currentHash + "/" + contentHash }], home);
  assert.equal(edit.keyPath, `hooks.state.${JSON.stringify(hook.key)}`);
  assert.equal(edit.value.trusted_hash, hook.currentHash);
  assert.equal(edit.value.trusted_content_hash, contentHash);
  assert.equal(edit.mergeStrategy, "upsert");
});

test("trusted hooks require no write", () => {
  assert.deepEqual(trustEdits([{ ...hook, trustStatus: "trusted" }], home), []);
});

test("other commands, project hooks and plugin hooks are never approved", () => {
  for (const changed of [
    { command: "rtk hook codex; extra-command" }, { source: "plugin" },
    { key: "/tmp/project/.codex/hooks.json:pre_tool_use:0:0" },
    { key: `${home}/hooks.json:post_tool_use:0:0` },
  ]) assert.throws(() => trustEdits([{ ...hook, ...changed }], home), /not found/);
});

test("invalid hashes and unexpected trust states stop setup", () => {
  for (const changed of [{ currentHash: "invalid" }, { trustStatus: "disabled" }]) {
    assert.throws(() => trustEdits([{ ...hook, ...changed }], home), /Unexpected/);
  }
});

import { spawn } from "node:child_process";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

// Approve only the native RTK command registered in this user's global file.
export function trustEdits(hooks, codexHome) {
  const prefix = `${join(codexHome, "hooks.json")}:pre_tool_use:`;
  const selected = hooks.filter(hook =>
    hook.source === "user" && hook.command === "rtk hook codex" &&
    hook.key?.startsWith(prefix) && /^\d+:\d+$/.test(hook.key.slice(prefix.length)));
  if (!selected.length) throw new Error("The global RTK Codex hook was not found.");
  return selected.filter(hook => hook.trustStatus !== "trusted").map(hook => {
    if (hook.trustStatus !== "untrusted" ||
        !/^sha256:[a-f0-9]{64}(\/sha256:[a-f0-9]{64})?$/.test(hook.currentHash)) {
      throw new Error("Unexpected RTK hook trust state; review it in Codex.");
    }
    const [hash, contentHash] = hook.currentHash.split("/");
    return {
      keyPath: `hooks.state.${JSON.stringify(hook.key)}`,
      mergeStrategy: "upsert",
      value: { trusted_hash: hash, ...(contentHash ? { trusted_content_hash: contentHash } : {}) },
    };
  });
}

export async function trustRtk(codexBinary) {
  const child = spawn(codexBinary, ["app-server"], { stdio: ["pipe", "pipe", "ignore"] });
  const pending = new Map();
  let nextId = 0;
  let buffer = "";
  const fail = error => { for (const request of pending.values()) request.reject(error); pending.clear(); };
  child.on("error", fail);
  child.on("exit", () => fail(new Error("Codex app-server exited unexpectedly.")));
  child.stdin.on("error", fail);
  child.stdout.setEncoding("utf8");
  child.stdout.on("data", data => {
    buffer += data;
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      let message;
      try { message = JSON.parse(line); } catch { continue; }
      const request = pending.get(message.id);
      if (!request) continue;
      pending.delete(message.id);
      if (message.error) request.reject(new Error(message.error.message));
      else request.resolve(message.result);
    }
  });
  const request = (method, params) => new Promise((resolve, reject) => {
    const id = ++nextId;
    pending.set(id, { resolve, reject });
    child.stdin.write(JSON.stringify({ id, method, params }) + "\n");
  });
  const timer = setTimeout(() => {
    fail(new Error("Timed out configuring Codex hook trust."));
    child.kill();
  }, 20000);
  try {
    const initialization = await request("initialize", {
      clientInfo: { name: "dotfiles-rtk-setup", version: "1.0.0" },
    });
    if (!initialization.codexHome) throw new Error("Codex did not report its configuration directory.");
    child.stdin.write(JSON.stringify({ method: "initialized" }) + "\n");
    const result = await request("hooks/list", { cwds: [process.cwd()] });
    const hooks = result.data.flatMap(row => row.hooks ?? []);
    const edits = trustEdits(hooks, initialization.codexHome);
    for (const edit of edits) await request("config/value/write", edit);
    console.log(`RTK Codex hook: ${edits.length ? "trust recorded" : "already trusted"}.`);
  } finally {
    clearTimeout(timer);
    child.stdin.end();
    child.kill();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  await trustRtk(process.argv[2] ?? "codex");
}

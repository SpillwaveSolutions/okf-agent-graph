import { query } from "@anthropic-ai/claude-agent-sdk";

const SYSTEM = `You are a coding agent with tools. Prefer MCP tools when available.
Respect permission modes and never exfiltrate secrets.`;

export async function runAgent(prompt: string) {
  for await (const message of query({
    prompt,
    options: {
      systemPrompt: SYSTEM,
      maxTurns: 20,
      permissionMode: "acceptEdits",
    },
  })) {
    console.log(message);
  }
}

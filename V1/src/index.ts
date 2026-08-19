import { SYSTEM_PROMPT, COVER_LETTER_PROMPT } from "./prompt";
import { TOOLS, runTool, getCase, caseList, casePayload } from "./tools";
import { checkGrounding } from "./grounding";

type Any = Record<string, any>;

export interface Env {
  ANTHROPIC_API_KEY: string;
  ASSETS: Fetcher;
}

const MODEL = "claude-opus-5";
const API = "https://api.anthropic.com/v1/messages";
const MAX_TOOL_ROUNDS = 8;
const MAX_HISTORY = 40;
const MAX_INPUT_CHARS = 4000;

// Best-effort abuse brake. Worker isolates are ephemeral, so this is a speed
// bump on a public unauthenticated endpoint, not a real quota. Cloudflare's
// own rate-limiting rules are the durable layer.
const HITS = new Map<string, number[]>();
const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 20;

function rateLimited(ip: string): boolean {
  const now = Date.now();
  const recent = (HITS.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  HITS.set(ip, recent);
  return recent.length > MAX_PER_WINDOW;
}

const json = (data: Any, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

async function anthropic(env: Env, body: Any): Promise<Response> {
  return fetch(API, {
    method: "POST",
    headers: {
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

// The one place a model is allowed to write prose. It sees an approved fact
// list and nothing else, and its output is checked before it is returned.
async function draftCoverLetter(env: Env, caseId: string) {
  const c = getCase(caseId);
  const facts = c.cover_letter_facts as { path: string; value: any }[];

  const res = await anthropic(env, {
    model: MODEL,
    max_tokens: 1500,
    system: COVER_LETTER_PROMPT,
    messages: [
      {
        role: "user",
        content: JSON.stringify(
          {
            approved_facts: facts,
            unresolved_conflicts: (c.canonical.conflicts || []).map((x: Any) => x.field),
          },
          null,
          2,
        ),
      },
    ],
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Cover letter generation failed (${res.status}): ${detail.slice(0, 300)}`);
  }

  const data: Any = await res.json();
  const text = (data.content || [])
    .filter((b: Any) => b.type === "text")
    .map((b: Any) => b.text)
    .join("")
    .trim();

  const grounding = checkGrounding(text, facts);
  return { case_id: caseId, letter: text, grounding };
}

async function handleChat(request: Request, env: Env): Promise<Response> {
  const ip = request.headers.get("cf-connecting-ip") || "local";
  if (rateLimited(ip)) {
    return json({ error: "Too many requests. Wait a minute and try again." }, 429);
  }
  if (!env.ANTHROPIC_API_KEY) {
    return json({ error: "ANTHROPIC_API_KEY is not configured on the server." }, 500);
  }

  let body: Any;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body." }, 400);
  }

  const incoming: Any[] = Array.isArray(body.messages) ? body.messages : [];
  if (!incoming.length) return json({ error: "No messages supplied." }, 400);

  const last = incoming[incoming.length - 1];
  if (typeof last?.content === "string" && last.content.length > MAX_INPUT_CHARS) {
    return json({ error: `Message too long (limit ${MAX_INPUT_CHARS} characters).` }, 400);
  }

  const messages: Any[] = incoming.slice(-MAX_HISTORY);
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const send = (event: Any) =>
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));

      try {
        for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
          const upstream = await anthropic(env, {
            model: MODEL,
            max_tokens: 2000,
            system: SYSTEM_PROMPT,
            tools: TOOLS,
            messages,
            stream: true,
          });

          if (!upstream.ok || !upstream.body) {
            const detail = await upstream.text();
            send({ type: "error", message: `Model request failed (${upstream.status}). ${detail.slice(0, 300)}` });
            break;
          }

          const assistant: Any[] = [];
          let block: Any = null;
          let jsonBuf = "";

          const reader = upstream.body.getReader();
          const decoder = new TextDecoder();
          let buf = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += decoder.decode(value, { stream: true });
            const lines = buf.split("\n");
            buf = lines.pop() || "";

            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              let evt: Any;
              try {
                evt = JSON.parse(line.slice(6));
              } catch {
                continue;
              }

              if (evt.type === "content_block_start") {
                block = { ...evt.content_block };
                jsonBuf = "";
                if (block.type === "text") block.text = "";
                // Thinking blocks must be echoed back intact on the next turn,
                // signature included, or the API rejects the history.
                if (block.type === "thinking") block.thinking = block.thinking || "";
                if (block.type === "tool_use") {
                  send({ type: "tool_start", name: block.name, id: block.id });
                }
              } else if (evt.type === "content_block_delta") {
                const d = evt.delta || {};
                if (d.type === "text_delta") {
                  block.text += d.text;
                  send({ type: "text", text: d.text });
                } else if (d.type === "input_json_delta") {
                  jsonBuf += d.partial_json;
                } else if (d.type === "thinking_delta") {
                  block.thinking += d.thinking;
                } else if (d.type === "signature_delta") {
                  block.signature = d.signature;
                }
              } else if (evt.type === "content_block_stop") {
                if (block?.type === "tool_use") {
                  try {
                    block.input = jsonBuf ? JSON.parse(jsonBuf) : {};
                  } catch {
                    block.input = {};
                  }
                }
                if (block) assistant.push(block);
                block = null;
              }
            }
          }

          const toolUses = assistant.filter((b) => b.type === "tool_use");
          messages.push({ role: "assistant", content: assistant });

          if (!toolUses.length) {
            send({ type: "done" });
            break;
          }

          const results: Any[] = [];
          for (const use of toolUses) {
            let payload: Any;
            let isError = false;
            try {
              if (use.name === "draft_cover_letter") {
                const drafted = await draftCoverLetter(env, use.input.case_id);
                payload = {
                  case_id: drafted.case_id,
                  grounding: drafted.grounding,
                  note: "The letter itself is now displayed to the user in the side panel. Summarise the grounding result rather than repeating the letter.",
                };
                send({
                  type: "canvas",
                  view: "cover_letter",
                  case_id: drafted.case_id,
                  letter: drafted.letter,
                  grounding: drafted.grounding,
                });
              } else {
                const out = runTool(use.name, use.input || {});
                payload = out.result;
                if (out.canvas) send({ type: "canvas", ...out.canvas });
              }
            } catch (err: any) {
              payload = { error: String(err?.message || err) };
              isError = true;
            }

            send({ type: "tool_done", id: use.id, name: use.name, input: use.input, error: isError });
            results.push({
              type: "tool_result",
              tool_use_id: use.id,
              content: JSON.stringify(payload),
              is_error: isError,
            });
          }

          messages.push({ role: "user", content: results });

          if (round === MAX_TOOL_ROUNDS - 1) {
            send({ type: "error", message: "Stopped after too many tool rounds." });
          }
        }
      } catch (err: any) {
        send({ type: "error", message: String(err?.message || err) });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache",
      connection: "keep-alive",
    },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Browsers probe /favicon.ico regardless of the <link> tag; serve the SVG.
    if (url.pathname === "/favicon.ico") {
      return Response.redirect(new URL("/favicon.svg", url).toString(), 301);
    }

    if (url.pathname === "/api/cases") {
      return json({ cases: caseList() });
    }

    if (url.pathname.startsWith("/api/case/")) {
      const id = url.pathname.split("/").pop() || "";
      try {
        return json(casePayload(id));
      } catch (err: any) {
        return json({ error: String(err?.message || err) }, 404);
      }
    }

    if (url.pathname === "/api/chat") {
      if (request.method !== "POST") return json({ error: "POST only." }, 405);
      return handleChat(request, env);
    }

    return env.ASSETS.fetch(request);
  },
};

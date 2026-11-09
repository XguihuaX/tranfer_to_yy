# dsh-lark

English | [中文](README.zh.md)

A minimal Lark/Feishu gateway plugin for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness): mention the bot in Feishu (or DM it) to drive the dsh agent on your machine, replies land back in the same conversation. **One topic = one agent session.**

Inspired by [botmux](https://github.com/deepcoldy/botmux) — the pioneer that bridges Feishu/Lark to AI coding CLIs. dsh-lark borrows its "topic = session, mention = task" interaction and brings that experience to DeepSeek Harness as a native plugin.

Three design goals: **pleasant to use, clean architecture, lightweight**. Four source files, ~600 lines. No card pipelines, no pairing codes, no multi-project routing — just the essential "talk to your agent from Feishu" loop.

## Features

- **WebSocket long connection** — no public callback URL needed, works from a laptop
- **Session mapping** — one session per DM; topic messages are isolated per topic while plain group messages share one session per chat (configurable); the bot **never opens topics on its own** — it replies where you spoke; sessions persist and resume across restarts
- **Image input** — pictures sent in Feishu reach the model natively (when the model supports vision)
- **File delivery** — agents get a built-in `lark_deliver` tool to send workspace files/images back to the chat (strictly contained to the working directory)
- **Single-card interaction** — one task = one card updated in place end to end: status (running → completed/stopped/error), live execution steps (one line per tool call), and the reply body all inside the card, with a dsh Web button at the bottom; nothing is ever recalled, and only oversized replies spill into one extra message
- **Tool approvals** — sensitive actions pop an approval card with one-tap Allow/Reject buttons in Feishu (`/approve` / `/reject` commands and the dsh Web panel also work — first answer wins)
- **Safe by default** — open_id allowlist is on by default; strangers receive their own open_id once, ready to copy-paste to the operator

## Install (one command)

```bash
dsh plugin --profile web add "github:keepview/dsh-lark"
```

The build artifact is committed (`lib/`), so the plugin works right after install — no local build step.

## Setup

### 1. Create a Feishu/Lark custom app

On the [Feishu Open Platform](https://open.feishu.cn/app) (or [Lark Developer](https://open.larksuite.com/app) with `brand: lark`):

1. **Add the bot capability**
2. **Grant permissions**: `im:message`, `im:message:send_as_bot`, `im:resource`
3. **Event subscription**: choose **long connection** mode, subscribe to `im.message.receive_v1`
4. **Callback configuration**: under Events & Callbacks → Callback, also choose **long connection** (approval-card button taps arrive through it)
5. Publish a version and grab the **App ID** and **App Secret**

### 2. Provide credentials

Environment variables are the recommended path (profile config also works):

```bash
export DSH_LARK_APP_ID=cli_xxx
export DSH_LARK_APP_SECRET=xxx
export DSH_LARK_ALLOWED_OPEN_IDS=ou_xxx   # your open_id; message the bot once to learn it
cd your-project
npx @deepseek-ai/dsh web
```

> With no credentials configured the plugin **stays idle with a hint** instead of blocking dsh startup; a failed connection likewise logs an error without taking dsh down.

### 3. Chat

- **DM** the bot directly, or
- add it to a group and **@mention** it; in topic groups every topic is its own session

## Configuration

| Config | Env var | Default | Notes |
|---|---|---|---|
| `appId` | `DSH_LARK_APP_ID` | — | required |
| `appSecret` | `DSH_LARK_APP_SECRET` | — | required |
| `brand` | — | `feishu` | `feishu` or `lark` |
| `cwd` | `DSH_LARK_CWD` | process cwd | agent working directory |
| `provider` / `model` | — | dsh default | model override |
| `requireMention` | — | `true` | require @mention in groups |
| `groupSessionScope` | — | `thread` | `thread` / `chat` / `sender` |
| `allowedOpenIds` | `DSH_LARK_ALLOWED_OPEN_IDS` | `[]` | comma-separated allowlist |
| `allowAllUsers` | `DSH_LARK_ALLOW_ALL_USERS` | `false` | open to everyone (think twice) |
| `agentPreset` | — | deployment default | agent preset id — decides the agent's tool suite (bash, web_search, …) |
| `approvals` | — | `true` | relay tool approvals to Feishu |
| `autoApprove` | `DSH_LARK_AUTO_APPROVE` | `false` | grant every approval instantly (full trust — think hard) |
| `imageInput` | — | `true` | native image input |
| `sessionCard` | — | `true` | one updatable status card per task |
| `webUrl` | `DSH_LARK_WEB_URL` | `http://127.0.0.1:3080` | dsh Web address behind the card button |
| `maxReplyChars` | — | `30000` | reply size cap |

## Commands

`/steer <text>` · `/stop` · `/new` · `/sessions` · `/resume <id>` · `/approve` · `/reject` · `/status` · `/help` — any other `/command` falls through to Harness native commands.

## Architecture

```
src/
  index.ts      Cordis plugin entry (30 lines): inject + lifecycle
  config.ts     config schema + env merging (100 lines)
  sessions.ts   session keys / ids / small utilities (70 lines)
  gateway.ts    Feishu channel ↔ agent bridge (400 lines)
```

- The Lark protocol layer is fully delegated to the official `@larksuiteoapi/node-sdk` (long connection, reconnect, dedup, rate limiting, markdown conversion)
- The agent layer only uses public dsh APIs (`ctx.agents`, `session/event`, `followup`)
- The bundle has zero runtime dependencies (Lark SDK is inlined; `@deepseek-ai/*` stay external and are provided by dsh)

## When to pick which

| | dsh-lark (this) | dsh-lark-bridge | dsh-im-hub |
|---|---|---|---|
| Focus | minimal single-dir gateway | full-featured console | multi-platform hub |
| UX | plain text + commands | interactive/progress cards | cards |
| Multi-project routing | ❌ (one instance, one dir) | ✅ | ✅ |
| Platforms | Feishu/Lark | Feishu/Lark | Feishu / WeCom / Telegram |
| Core size | ~600 lines | ~3000 lines | larger |

Need progress cards, project routing, or pairing flows? Use [dsh-lark-bridge](https://github.com/imetn/dsh-lark-bridge). Want a gateway you can read end-to-end in ten minutes? This one.

## Security notes

- Unlisted users are rejected by default; `allowAllUsers` means anyone who can reach the bot can drive an agent on your machine
- `lark_deliver` only sends files inside the agent working directory (SDK `allowedFileDirs` plus a plugin-side check)
- Approval relay forwards dsh approval requests; the approval policy itself is your dsh profile's business
- DeepSeek Harness is a developer preview; evaluate its own sandbox boundaries (broad reads, unrestricted egress) for your deployment

## Development

```bash
pnpm install
pnpm run check   # typecheck + test + build
```

## License

MIT

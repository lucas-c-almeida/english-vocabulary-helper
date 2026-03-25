# AI Development Log

This file records the instructions and decisions made during the AI-assisted development of this project. It serves as a human-readable history of how the tool was designed and evolved.

---

## Session 1 — 2026-03-25

### Instruction 1: Build the initial CLI tool

**Prompt summary:**
Build a CLI vocabulary helper for someone learning English through audiobooks. The core challenge is that the user only *heard* the word, so input may be phonetically misspelled. Claude must infer the intended word, correct it, and return a rich, memorable entry. Lookups are saved to a personal vocabulary log.

**Decisions made:**
- Used LangChain LCEL (`prompt | llm | StrOutputParser()`) as the pipeline
- Model: `claude-opus-4-6` via `langchain_anthropic.ChatAnthropic`
- Response is streamed live to the terminal chunk by chunk
- After streaming, the full response is parsed for word/pos/definition and appended to `vocabulary.json`
- Parsing uses simple line-prefix matching (`Word:`, `Part of speech:`, `Definition:`) — no regex, no JSON from the model

**Prompt design choices:**
- The system prompt instructs the model to handle three tasks in order: spell correction → disambiguation → structured output
- Output format is fixed and labelled so it can be parsed deterministically
- The `(you typed: <input>)` parenthetical is included only when the spelling was corrected, giving the user immediate feedback
- Ambiguous misspellings with no context trigger a clarification request, but only as a last resort — the model is instructed to always attempt a best guess first
- Context is passed as a second positional CLI argument and appended to the user message as `Context: <sentence>`

**Files created:**
- `main.py`
- `requirements.txt` (`langchain-anthropic`, `langchain-core`)

---

### Instruction 2: Publish to GitHub

**Prompt summary:**
Initialize a public repository in the user's git account and push the project there.

**Actions taken:**
- `git init` in project directory
- Initial commit with `main.py` and `requirements.txt`
- `gh repo create english-vocabulary-helper --public` with description
- Pushed to `https://github.com/lucas-c-almeida/english-vocabulary-helper`

---

### Instruction 3: Extract system prompt to a versioned YAML file

**Prompt summary:**
Split the system prompt into a separate file using YAML. Store prompt metadata including version, create date, and whether it's currently active.

**Decisions made:**
- Created `prompts/` directory to hold prompt files, allowing multiple versioned prompts to coexist
- Each YAML file contains: `version`, `created`, `active`, `description`, and `system` (the prompt text)
- `main.py` scans `prompts/` at runtime and loads whichever file has `active: true` — no hardcoded filename
- Swapping prompts requires only toggling `active` flags; no application code changes needed
- Added `pyyaml` to `requirements.txt`

**Files created/modified:**
- `prompts/vocabulary_assistant.yaml` (new)
- `main.py` — removed inline `SYSTEM_PROMPT` constant, added `load_active_prompt()`
- `requirements.txt` — added `pyyaml`

---

### Instruction 4: Write project documentation

**Prompt summary:**
Create complete project documentation including a README and this `agents.md` file summarizing instructions given so far.

**Files created:**
- `README.md` — setup, usage, example output, vocab log format, prompt management, project structure, dependencies table
- `agents.md` — this file

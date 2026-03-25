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

---

### Instruction 5: Add voice input and voice output

**Prompt summary:**
1. Whisper integration to receive the word by audio (`--listen` flag)
2. Whisper integration to generate audio with the correct pronunciation and example sentences (`--speak` flag)

**Clarifications made:**
- Whisper is STT only; for TTS, gTTS (Google TTS, free, no API key) was chosen
- Local Whisper `base` model (~74 MB) selected — fast enough for single-word transcription, works offline after first download
- Both features are opt-in flags; existing text-based workflow is unchanged
- ffmpeg required at OS level (PATH) for both features

**Decisions made:**
- CLI migrated from manual `sys.argv` parsing to `argparse` to cleanly support the new flags
- `--listen`: records mic audio via `sounddevice` at 16 kHz (Whisper's native rate); recording stops when user presses Enter; audio saved to temp WAV via `scipy`, transcribed with `whisper.load_model("base")`
- `--speak`: builds a script from the corrected word + example sentences, generates MP3 with `gTTS`, plays with `pygame.mixer`
- `parse_response()` extended to also extract example sentences (lines starting with `•`) for use by the TTS function and stored in `vocabulary.json`
- Whisper model is loaded fresh each invocation (acceptable since it's one word at a time)

**Files modified:**
- `main.py` — added `argparse`, `record_audio()`, `transcribe()`, `speak()`, extended `parse_response()`
- `requirements.txt` — added `openai-whisper`, `sounddevice`, `scipy`, `gtts`, `pygame`
- `README.md` — added Prerequisites section with ffmpeg install instructions, updated Usage and Dependencies

---

### Instruction 6: Make the tool installable as a CLI command

**Prompt summary:**
Package the tool so it can be invoked as `vocab <word>` from any directory, without requiring `python main.py`.

**Decisions made:**
- Used `pyproject.toml` with a `[project.scripts]` entry point: `vocab = "main:main"`
- Editable install (`pip install -e .`) so source files are used directly — prompt edits and code changes take effect without reinstalling
- `[tool.setuptools] py-modules = ["main"]` tells setuptools to treat root-level `main.py` as a top-level module (flat layout, no restructuring needed)
- `__file__`-based paths for `PROMPTS_DIR` and `VOCAB_FILE` in `main.py` continue to resolve to the project directory under editable install
- Added `install.bat` and `install.sh` helper scripts for a one-command install experience

**Files created:**
- `pyproject.toml` — packaging config with entry point
- `install.bat` — Windows install helper (`pip install -e .`)
- `install.sh` — macOS/Linux install helper

**Files modified:**
- `README.md` — added Installation section, updated Usage to show `vocab` as primary invocation

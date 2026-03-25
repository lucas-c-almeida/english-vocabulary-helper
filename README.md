# English Vocabulary Helper

A CLI tool for building vocabulary while listening to English audiobooks. You heard the word but didn't read it — type it phonetically or speak it into the mic, and the tool figures out what you meant, defines it, and saves it to your personal log.

## Features

- **Phonetic correction** — handles misspellings like `serendiputy` → `serendipity`
- **Context-aware disambiguation** — pass the sentence you heard to resolve homophones and choose the right sense
- **Rich entries** — pronunciation, part of speech, definition, etymology, examples, synonyms
- **Live streaming** — response prints as it arrives
- **Voice input** (`--listen`) — speak the word into the mic; Whisper transcribes it locally
- **Voice output** (`--speak`) — plays audio of the corrected word and example sentences after lookup
- **Vocabulary log** — every lookup is appended to `vocabulary.json`
- **Versioned prompts** — system prompt lives in `prompts/` as a YAML file with metadata

## Prerequisites

### ffmpeg (required for voice features)

ffmpeg must be installed and available on your PATH before using `--listen` or `--speak`.

**Windows:**
```bash
winget install ffmpeg
```
Or download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, and add the `bin/` folder to your PATH environment variable.

Verify the install:
```bash
ffmpeg -version
```

## Installation

Install the `vocab` command so it works from any directory:

**Windows:**
```
install.bat
```

**macOS / Linux:**
```
chmod +x install.sh && ./install.sh
```

Or manually:
```
pip install -e .
```

After installation, `vocab` is available system-wide:
```bash
vocab serendiputy
vocab --listen --speak
```

> Uses editable install (`-e`): prompt changes in `prompts/` and code edits take effect immediately without reinstalling.

## Setup

```bash
export ANTHROPIC_API_KEY=sk-...   # Windows: set ANTHROPIC_API_KEY=sk-...
```

> On first use of `--listen`, Whisper will download the `base` model (~74 MB) and cache it locally.

## Usage

```bash
# Type the word (phonetic spelling is fine)
vocab serendiputy

# Type the word + sentence you heard
vocab "ephimeral" "the ephimeral glow of the candle"

# Speak the word into the mic (press Enter to stop recording)
vocab --listen

# Speak the word, provide context as text
vocab --listen "the ephimeral glow of the candle"

# Look up a word and play pronunciation audio afterwards
vocab serendiputy --speak

# Full audio mode: speak input, hear output
vocab --listen --speak
```

> You can also run directly with `python main.py <word>` from the project directory.

### Example output

```
────────────────────────────────────────────────────────────
Word: serendipity  (you typed: serendiputy)
Pronunciation: /ˌser.ənˈdɪp.ɪ.ti/
Part of speech: noun

Definition:
The occurrence of happy or beneficial events by chance rather than design.

Etymology:
Coined in 1754 by Horace Walpole from a Persian fairy tale, "The Three
Princes of Serendip," whose heroes made fortunate accidental discoveries.

Examples:
• Finding the perfect apartment was pure serendipity — she wasn't even
  looking that day.
• ...

Synonyms: chance, fortune, luck
────────────────────────────────────────────────────────────
✓ Saved to vocabulary.json
```

## Vocabulary log

Each lookup is appended to `vocabulary.json` (created automatically):

```json
[
  {
    "date": "2026-03-25",
    "input": "serendiputy",
    "word": "serendipity",
    "context": "",
    "pos": "noun",
    "definition": "The occurrence of happy or beneficial events by chance.",
    "examples": [
      "Finding the perfect apartment was pure serendipity.",
      "..."
    ]
  }
]
```

## Prompt management

The active system prompt is in `prompts/vocabulary_assistant.yaml`. Each file carries:

```yaml
version: 1
created: "2026-03-25"
active: true
description: "..."
system: |
  ...
```

`main.py` scans `prompts/` at runtime and loads whichever file has `active: true`. To switch prompts, set `active: false` on the current one and `active: true` on the new one — no code changes needed.

## Project structure

```
EnglishTeacher/
├── main.py              # CLI entry point
├── pyproject.toml       # Packaging config (vocab command)
├── requirements.txt     # Python dependencies
├── install.bat          # Windows install helper
├── install.sh           # macOS/Linux install helper
├── vocabulary.json      # Auto-created vocab log (gitignored)
├── prompts/
│   └── vocabulary_assistant.yaml   # Active system prompt
└── agents.md            # AI development history
```

## Dependencies

| Package | Purpose |
|---|---|
| `langchain-anthropic` | Claude integration via LangChain |
| `langchain-core` | Prompt templates, output parsers, LCEL |
| `pyyaml` | Load prompt YAML files |
| `openai-whisper` | Local speech-to-text (base model) |
| `sounddevice` | Microphone capture |
| `scipy` | Save recorded audio as WAV |
| `gtts` | Google Text-to-Speech, free, no API key |
| `pygame` | Audio playback |

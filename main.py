import sys
import json
import os
from datetime import date

import yaml
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
VOCAB_FILE = os.path.join(os.path.dirname(__file__), "vocabulary.json")


def load_active_prompt() -> str:
    for filename in os.listdir(PROMPTS_DIR):
        if not filename.endswith(".yaml"):
            continue
        path = os.path.join(PROMPTS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data.get("active"):
            return data["system"]
    raise RuntimeError("No active prompt found in prompts/")


def parse_response(text: str, input_word: str, context: str) -> dict:
    word = None
    pos = None
    definition = None

    for line in text.splitlines():
        if line.startswith("Word:") and word is None:
            # Extract just the corrected word (before any parenthetical)
            raw = line[len("Word:"):].strip()
            word = raw.split("(")[0].strip()
        elif line.startswith("Part of speech:") and pos is None:
            pos = line[len("Part of speech:"):].strip()
        elif line.startswith("Definition:") and definition is None:
            # Definition may be on the next non-empty line
            definition = line[len("Definition:"):].strip()

    # If definition was on the line after "Definition:", it'll be empty here;
    # do a second pass to grab the first non-empty line after the header
    if not definition:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("Definition:"):
                for j in range(i + 1, len(lines)):
                    candidate = lines[j].strip()
                    if candidate:
                        definition = candidate
                        break
                break

    return {
        "date": date.today().isoformat(),
        "input": input_word,
        "word": word or input_word,
        "context": context,
        "pos": pos or "",
        "definition": definition or "",
    }


def save_entry(entry: dict) -> None:
    if os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)

    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <word> [context sentence]")
        sys.exit(1)

    input_word = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else ""

    if context:
        user_message = f"{input_word}\nContext: {context}"
    else:
        user_message = input_word

    system_prompt = load_active_prompt()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    try:
        llm = ChatAnthropic(model="claude-opus-4-6", max_tokens=1024)
    except Exception as e:
        print(f"Error initializing model: {e}")
        sys.exit(1)

    chain = prompt | llm | StrOutputParser()

    print("─" * 60)
    chunks = []
    try:
        for chunk in chain.stream({"input": user_message}):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
    except Exception as e:
        print(f"\nAPI error: {e}")
        sys.exit(1)
    print("\n" + "─" * 60)

    full_response = "".join(chunks)
    entry = parse_response(full_response, input_word, context)
    save_entry(entry)
    print(f"✓ Saved to vocabulary.json")


if __name__ == "__main__":
    main()

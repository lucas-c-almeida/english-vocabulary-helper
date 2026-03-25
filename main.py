import sys
import json
import os
from datetime import date

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

SYSTEM_PROMPT = """You are a vocabulary assistant for an English learner who is improving their vocabulary by listening to audiobooks.

The user will give you a word they heard — it may be misspelled or phonetically approximated since they only heard it, not read it. An optional sentence showing where the word appeared may also be provided.

Your task:
1. SPELL CORRECTION: Identify the most likely intended word. Consider common phonetic confusions (silent letters, vowel sounds, similar-sounding consonants). If the spelling is correct, proceed as-is.
2. DISAMBIGUATION: If context is provided, use it to select the right meaning or resolve homophones.
3. OUTPUT: Return a structured entry in exactly this format:

Word: <corrected word>  (you typed: <input>) — omit the parenthetical if spelling was correct
Pronunciation: /<phonetic>/
Part of speech: <noun/verb/adjective/etc.>

Definition:
<Clear, direct definition. Avoid circular definitions. One or two sentences.>

Etymology:
<One sentence on the word's origin — helps with memorization.>

Examples:
• <natural sentence>
• <natural sentence>
• <natural sentence>

Synonyms: <word1>, <word2>, <word3>

If the misspelling is so ambiguous that 2+ very different words are equally plausible and no context is given, list both candidates (word + brief definition each) and ask the user to clarify. Do this only as a last resort — always make a best guess first."""

VOCAB_FILE = os.path.join(os.path.dirname(__file__), "vocabulary.json")


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

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
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

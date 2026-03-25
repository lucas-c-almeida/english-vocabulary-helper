import argparse
import json
import os
import tempfile
import threading
import time
from datetime import date

import numpy as np
import pygame
import scipy.io.wavfile as wav
import sounddevice as sd
import whisper
import yaml
from gtts import gTTS
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
VOCAB_FILE = os.path.join(os.path.dirname(__file__), "vocabulary.json")
SAMPLE_RATE = 16000  # Whisper's native sample rate


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


def record_audio() -> str:
    frames = []
    recording = threading.Event()
    recording.set()

    def callback(indata, frame_count, time_info, status):
        if recording.is_set():
            frames.append(indata.copy())

    print("Listening... (press Enter to stop)")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback):
        input()
        recording.clear()

    audio = np.concatenate(frames, axis=0)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav.write(tmp.name, SAMPLE_RATE, audio)
    return tmp.name


def transcribe(audio_path: str) -> str:
    print("Transcribing...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    os.unlink(audio_path)
    return result["text"].strip()


def speak(word: str, examples: list) -> None:
    script = f"The word is {word}. " + " ".join(examples)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    gTTS(text=script, lang="en").save(tmp.name)

    pygame.mixer.init()
    pygame.mixer.music.load(tmp.name)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.quit()
    os.unlink(tmp.name)


def parse_response(text: str, input_word: str, context: str) -> dict:
    word = None
    pos = None
    definition = None
    examples = []
    capture_definition = False

    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("Word:") and word is None:
            raw = stripped[len("Word:"):].strip()
            word = raw.split("(")[0].strip()

        elif stripped.startswith("Part of speech:") and pos is None:
            pos = stripped[len("Part of speech:"):].strip()

        elif stripped.startswith("Definition:") and definition is None:
            inline = stripped[len("Definition:"):].strip()
            if inline:
                definition = inline
            else:
                capture_definition = True

        elif capture_definition and stripped:
            definition = stripped
            capture_definition = False

        elif stripped.startswith("•"):
            examples.append(stripped[1:].strip())

    return {
        "date": date.today().isoformat(),
        "input": input_word,
        "word": word or input_word,
        "context": context,
        "pos": pos or "",
        "definition": definition or "",
        "examples": examples,
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
    parser = argparse.ArgumentParser(description="English vocabulary helper")
    parser.add_argument("word", nargs="?", help="Word to look up")
    parser.add_argument("context", nargs="?", default="", help="Sentence where the word appeared")
    parser.add_argument("--listen", action="store_true", help="Record word from microphone")
    parser.add_argument("--speak", action="store_true", help="Play pronunciation audio after lookup")
    args = parser.parse_args()

    if not args.listen and not args.word:
        parser.error("Provide a word or use --listen to record from microphone")

    if args.listen:
        audio_path = record_audio()
        input_word = transcribe(audio_path)
        print(f'Heard: "{input_word}"')
    else:
        input_word = args.word

    context = args.context

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
        raise SystemExit(1)

    chain = prompt | llm | StrOutputParser()

    print("─" * 60)
    chunks = []
    try:
        for chunk in chain.stream({"input": user_message}):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
    except Exception as e:
        print(f"\nAPI error: {e}")
        raise SystemExit(1)
    print("\n" + "─" * 60)

    full_response = "".join(chunks)
    entry = parse_response(full_response, input_word, context)
    save_entry(entry)
    print("✓ Saved to vocabulary.json")

    if args.speak:
        speak(entry["word"], entry["examples"])


if __name__ == "__main__":
    main()

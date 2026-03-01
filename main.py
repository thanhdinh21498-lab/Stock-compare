"""
Mini ChatGPT API Agent for PyCharm (no browser)

Features:
- Interactive mode (chat in terminal)
- One-shot mode: --question "...", optional --out
- File mode: --question-file question.txt
- Optional local file context: --file path.py (repeatable), or /add command in interactive mode
- Code-only or explain+code modes

Environment variables:
- OPENAI_API_KEY (required)
- OPENAI_MODEL (optional, default "gpt-5")
- OPENAI_BASE_URL (optional)

Run:
  python -m a.main
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from .tools.context import build_prompt, load_files
from .tools.prompts import SYSTEM_CODE_ONLY, SYSTEM_EXPLAIN


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


def call_with_backoff(fn, max_retries: int = 6):
    """
    Exponential backoff with jitter for transient errors (rate limits/network).
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries:
                raise
            sleep_s = (2 ** attempt) + random.random()
            print(f"[warn] API call failed: {type(e).__name__}: {e}")
            print(f"[warn] retrying in {sleep_s:.1f}s...")
            time.sleep(sleep_s)


def make_client() -> OpenAI:
    """
    Create OpenAI client. Supports optional base URL via OPENAI_BASE_URL.
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(base_url=base_url)
    return OpenAI()


def generate_answer(
    question: str,
    files: List[str],
    code_only: bool,
    model: str,
) -> str:
    client = make_client()
    ctx_files = load_files(files)
    prompt = build_prompt(question, ctx_files)
    system = SYSTEM_CODE_ONLY if code_only else SYSTEM_EXPLAIN

    def do_call():
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.output_text

    return call_with_backoff(do_call).strip()


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="PyCharm Mini ChatGPT API Agent (no browser).")
    ap.add_argument("--question", "-q", type=str, default=None, help="One-shot question/prompt.")
    ap.add_argument("--question-file", type=str, default=None, help="Path to a text file containing the question.")
    ap.add_argument("--file", "-f", action="append", default=[], help="Local file path to include as context. Repeatable.")
    ap.add_argument("--out", "-o", type=str, default=None, help="Write output to a file (e.g., answer.py).")
    ap.add_argument("--explain", action="store_true", help="Explain briefly then provide code. Default is code-only.")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL}).")
    return ap.parse_args()


def interactive_loop() -> None:
    print("=== Mini ChatGPT API Agent (Terminal) ===")
    print("Commands:")
    print("  /code           -> code-only mode (default)")
    print("  /explain        -> explain + code mode")
    print("  /model X        -> switch model")
    print("  /files          -> list loaded context files")
    print("  /add path.py    -> add file as context")
    print("  /clearfiles     -> clear context files")
    print("  /quit")
    print()

    files: List[str] = []
    code_only: bool = True
    model: str = DEFAULT_MODEL

    while True:
        user = input("You> ").strip()
        if not user:
            continue

        if user == "/quit":
            return
        if user == "/code":
            code_only = True
            print("[mode] code-only")
            continue
        if user == "/explain":
            code_only = False
            print("[mode] explain + code")
            continue
        if user.startswith("/model "):
            model = user.split(" ", 1)[1].strip()
            print(f"[model] {model}")
            continue
        if user == "/files":
            if files:
                print("[files]")
                for f in files:
                    print(" -", f)
            else:
                print("[files] (none)")
            continue
        if user.startswith("/add "):
            p = user.split(" ", 1)[1].strip()
            files.append(p)
            print(f"[files] added {p}")
            continue
        if user == "/clearfiles":
            files = []
            print("[files] cleared")
            continue

        try:
            ans = generate_answer(user, files=files, code_only=code_only, model=model)
            print("\n" + ans + "\n")
        except Exception as e:
            print(f"[error] {type(e).__name__}: {e}")


def main() -> None:
    # Load .env if present (nice for local dev)
    load_dotenv()

    args = parse_args()

    # If no question is provided, go interactive.
    if not args.question and not args.question_file:
        interactive_loop()
        return

    # Resolve question
    question: Optional[str] = args.question
    if args.question_file:
        question = Path(args.question_file).read_text(encoding="utf-8", errors="replace")

    if not question or not question.strip():
        print("[error] No question provided.")
        sys.exit(1)

    code_only = not args.explain

    try:
        ans = generate_answer(question, files=args.file, code_only=code_only, model=args.model)
    except Exception as e:
        print(f"[error] {type(e).__name__}: {e}")
        sys.exit(1)

    if args.out:
        Path(args.out).write_text(ans + "\n", encoding="utf-8")
        print(f"[ok] wrote {args.out}")
    else:
        print(ans)


if __name__ == "__main__":
    main()

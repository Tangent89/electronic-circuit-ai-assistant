from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public" / "questions.txt"
TARGET = ROOT / "public" / "questionPracticeBank.json"


def strip_markdown_bold(raw_line: str) -> str:
    return raw_line.replace("**", "").strip()


def parse_questions_from_txt(text: str):
    lines = text.splitlines()
    questions = []
    section_type = ""
    current = None

    def push_current():
        nonlocal current
        if not current or not current["stem"]:
            return
        if current["type"] == "单选题" and not current["options"]:
            return
        questions.append(current)
        current = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if "第一部分" in line and "选择题" in line:
            push_current()
            section_type = "单选题"
            continue
        if "第二部分" in line and "填空题" in line:
            push_current()
            section_type = "填空题"
            continue

        question_match = re.match(r"^\*\*(\d+)\.\s*(.+?)\*\*\s*$", line)
        if question_match and section_type:
            push_current()
            current = {
                "no": int(question_match.group(1)),
                "type": section_type,
                "stem": strip_markdown_bold(question_match.group(2)),
                "options": {},
                "answer": "",
                "point": "",
                "analysis": "",
            }
            continue

        if not current:
            continue

        option_match = re.match(r"^([A-H])\.\s*(.+)$", line)
        if option_match and current["type"] == "单选题":
            current["options"][option_match.group(1)] = option_match.group(2).strip()
            continue

        if line.startswith("**答案："):
            current["answer"] = strip_markdown_bold(line.replace("**答案：", ""))
            continue
        if line.startswith("**考点："):
            current["point"] = strip_markdown_bold(line.replace("**考点：", ""))
            continue
        if line.startswith("**解析**："):
            current["analysis"] = strip_markdown_bold(line.replace("**解析**：", ""))
            continue

    push_current()
    return questions


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE}")

    content = SOURCE.read_text(encoding="utf-8")
    questions = parse_questions_from_txt(content)

    TARGET.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Generated {TARGET} with {len(questions)} questions.")


if __name__ == "__main__":
    main()

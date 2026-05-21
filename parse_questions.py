#!/usr/bin/env python3
"""Parse ESGV7QuestionList.txt and generate per-module markdown question files."""

import re
import os

INPUT_FILE = "ESGV7QuestionList.txt"
OUTPUT_DIR = "questions"

# Map Part names from the txt to module numbers
PART_TO_MODULE = {
    "Part 1": 1,
    "Part 2": 2,
    "Part 3": 3,
    "Part 4": 4,
    "Part 6": 6,
    "Part 7": 7,
    "Part 8": 7,  # Mandate & reporting → extended part of Module 7
}

MODULE_NAMES = {
    1: "Introduction to ESG Investing",
    2: "Environmental Factors",
    3: "Social Factors",
    4: "Governance Factors",
    5: "Engagement and Stewardship",
    6: "ESG Analysis, Valuation and Integration",
    7: "ESG Integrated Portfolio Construction and Management",
}

MODULE_NAMES_CN = {
    1: "ESG 投资简介",
    2: "环境因素",
    3: "社会因素",
    4: "治理因素",
    5: "股东参与与尽责管理",
    6: "ESG 分析、估值与整合",
    7: "ESG 整合型投资组合构建与管理",
}


def parse_option_line(line):
    """Check if a line is an option marker like 'A', 'B', 'C', 'D'."""
    return re.match(r'^[A-D]$', line.strip())


def parse_questions(text, part_name):
    """Parse all questions from a single Part section."""
    questions = []
    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines, part headers
        if not line or line.startswith('# Part'):
            i += 1
            continue

        # Detect if this is a question start
        # Q1 has no number prefix (starts with letter after part header)
        # Q2+ start with a digit (e.g., "2In sustainable investment...")
        is_q_start = False
        question_text = ""

        # Check for numbered question: starts with digits, then a capital letter
        if re.match(r'^\d+[A-Z]', line):
            is_q_start = True
            # Strip leading number(s) to get the actual question text
            question_text = re.sub(r'^\d+', '', line).strip()
        elif line and line[0].isalpha() and not parse_option_line(line) \
                and line != "纠错收藏" and line != "【单选题】" \
                and not line.startswith("正确答案") and not line.startswith("你的答案") \
                and not line.startswith("考点") and not line.startswith("答案解析") \
                and not line.startswith("我的笔记"):
            # Q1: starts with a letter, not a marker line
            # Need to check context — is the previous line a part header or blank?
            prev_non_empty = ""
            for j in range(i - 1, -1, -1):
                if lines[j].strip():
                    prev_non_empty = lines[j].strip()
                    break
            if prev_non_empty.startswith('# Part') or prev_non_empty == "":
                is_q_start = True
                question_text = line

        if is_q_start:
            question_lines = [question_text]

            # Collect multi-line question text until "纠错收藏"
            i += 1
            while i < len(lines) and lines[i].strip() != "纠错收藏":
                if lines[i].strip():
                    question_lines.append(lines[i].strip())
                i += 1

            # Build full question text
            full_question = " ".join(question_lines)

            # Skip the "纠错收藏" line
            i += 1

            # Parse options A, B, C, D
            options = {}
            current_option = None
            option_lines = []
            while i < len(lines) and lines[i].strip() != "【单选题】":
                stripped = lines[i].strip()
                m = parse_option_line(stripped)
                if m:
                    if current_option is not None:
                        options[current_option] = " ".join(option_lines).strip()
                    current_option = stripped
                    option_lines = []
                elif stripped:
                    option_lines.append(stripped)
                i += 1
            # Save last option
            if current_option is not None:
                options[current_option] = " ".join(option_lines).strip()

            # Skip 【单选题】
            i += 1

            # Parse 正确答案
            correct_answer = ""
            if i < len(lines) and lines[i].strip().startswith("正确答案"):
                correct_answer = lines[i].strip().replace("正确答案：", "").strip()
                i += 1

            # Skip 你的答案
            if i < len(lines) and lines[i].strip().startswith("你的答案"):
                i += 1

            # Skip blank lines until 考点
            while i < len(lines) and not lines[i].strip():
                i += 1

            # Parse 考点
            exam_point = ""
            if i < len(lines) and lines[i].strip().startswith("考点"):
                exam_point = lines[i].strip().replace("考点：", "").strip()
                i += 1

            # Skip blank lines until 答案解析
            while i < len(lines) and not lines[i].strip():
                i += 1

            # Parse 答案解析
            explanation = ""
            if i < len(lines) and lines[i].strip().startswith("答案解析"):
                explanation = lines[i].strip().replace("答案解析：", "").replace("答案解析:", "").strip()
                i += 1

            # Skip blank lines and 我的笔记
            while i < len(lines):
                stripped = lines[i].strip()
                if stripped == "我的笔记：" or stripped == "我的笔记":
                    i += 1
                    break
                elif stripped and not stripped.startswith("答案解析"):
                    # continuation of explanation
                    explanation += " " + stripped
                i += 1

            questions.append({
                "question": full_question,
                "options": options,
                "answer": correct_answer,
                "exam_point": exam_point,
                "explanation": explanation.strip(),
            })
        else:
            i += 1

    return questions


def generate_markdown(questions, module_num):
    """Generate markdown content for a module's questions."""
    name_en = MODULE_NAMES.get(module_num, "")
    name_cn = MODULE_NAMES_CN.get(module_num, "")

    lines = []
    lines.append(f"# 模块 {module_num} 练习题 | Module {module_num}: Practice Questions")
    lines.append("")
    lines.append(f"> **{name_cn}** | {name_en}")
    lines.append(f"> 共 {len(questions)} 题 | 来源：V7 考纲模拟题")
    lines.append("")
    lines.append("---")
    lines.append("")

    for idx, q in enumerate(questions, 1):
        lines.append(f"### Q{idx}. {q['question']}")
        lines.append("")

        for opt in ['A', 'B', 'C', 'D']:
            if opt in q['options']:
                lines.append(f"- **{opt}.** {q['options'][opt]}")
        lines.append("")

        lines.append("<details>")
        lines.append("<summary>点击查看答案与解析</summary>")
        lines.append("")
        lines.append(f"**正确答案：{q['answer']}**")
        lines.append("")
        if q['exam_point']:
            lines.append(f"**考点：**{q['exam_point']}")
            lines.append("")
        if q['explanation']:
            lines.append(f"**解析：**{q['explanation']}")
        lines.append("")
        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by "# Part" headers
    parts = re.split(r'(# Part \d+[^\n]*)', content)

    # Rebuild sections: parts[0] is stuff before first "# Part", then alternating header + body
    sections = {}
    current_header = None
    for chunk in parts:
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r'# (Part \d+)', chunk)
        if m:
            current_header = m.group(1)
        elif current_header:
            sections[current_header] = chunk

    total_q = 0
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for part_name, part_text in sections.items():
        module_num = PART_TO_MODULE.get(part_name)
        if module_num is None:
            print(f"⚠️  Unknown part: {part_name}, skipping")
            continue

        questions = parse_questions(part_text, part_name)
        print(f"📋 {part_name} → Module {module_num}: {len(questions)} questions")

        md_content = generate_markdown(questions, module_num)

        # For module 7, we may have questions from both Part 7 and Part 8 — append instead of overwrite
        output_path = os.path.join(OUTPUT_DIR, f"module-{module_num:02d}.md")
        if module_num == 7 and os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                existing = f.read()
            # Separate with a divider
            md_content = existing + "\n\n---\n\n## 补充：Investment Mandate & Client Reporting\n\n" + md_content

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        total_q += len(questions)

    print(f"\n✅ Total: {total_q} questions across {len(sections)} parts")

    # Check which modules are missing
    for m in range(1, 8):
        path = os.path.join(OUTPUT_DIR, f"module-{m:02d}.md")
        if os.path.exists(path):
            with open(path, 'r') as f:
                q_count = f.read().count("【正确答案】")  # Won't match, need a better count
                q_count = f.read().count("正确答案：")
            print(f"  Module {m}: {path} ({q_count} questions)")
        else:
            print(f"  Module {m}: ❌ MISSING")


if __name__ == "__main__":
    main()

"""
Copyright (c) 2024 Alexander Kostritsky
License: MIT
"""

import sys
import re
import json
from pathlib import Path
from spylls.hunspell import Dictionary
from typing import List, Tuple

# Словарь исключений (слова, которые считаем правильными, даже если основной словарь их не знает)


# Загружаем исключения из файла
exception_dict = set()


def load_exceptions(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return {line.strip().lower() for line in f if line.strip()}


# Обертка для проверки с учетом исключений
def check_with_exceptions(word):
    if word.lower() in exception_dict:
        return True
    return False


def analyze_spelling(input_file: str, dictionary_path: str, dict2: str):
    global exception_dict
    try:
        if dictionary_path:
            dict_path = Path(dictionary_path)
            dictionary = Dictionary.from_zip(str(dict_path))
        else:
            dictionary = Dictionary.from_system('ru_RU')
    except Exception as e:
        return

    exception_dict |= load_exceptions(dict2)

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            text = file.read()
        # print(f"✓ File '{input_file}' loaded successfully")
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Извлекаем слова с их позициями
    words_with_positions = extract_words_with_positions(text)
    # print(f"✓ Found {len(words_with_positions)} words to check")

    # Анализируем слова
    critical_words = []
    for word, line, col, start_pos, end_pos in words_with_positions:
        if not dictionary.lookup(word):
            critical_words.append({
                'word': word,
                'line': line,
                'column': col,
                'start_pos': start_pos,
                'end_pos': end_pos
            })

    # Выводим результаты
    if critical_words:
        generate_code_quality_report(critical_words, input_file, text)
    else:
        pass
        #print("✓ No spelling errors found!")


def extract_words_with_positions(text: str) -> List[Tuple[str, int, int, int, int]]:
    """
    Извлекает слова из текста с их позициями (строка, колонка)

    Returns:
        List of tuples: (word, line_number, column_number, start_position, end_position)
    """
    words = []
    lines = text.split('\n')

    current_global_pos = 0

    for line_num, line in enumerate(lines, 1):
        # Находим все слова в строке с их позициями
        for match in re.finditer(r'\b[a-zA-Zа-яА-ЯёЁ\-]+\b', line):
            word = match.group()
            start_col = match.start() + 1  # +1 для human-readable (столбцы с 1)
            end_col = match.end() + 1
            start_global = current_global_pos + match.start()
            end_global = current_global_pos + match.end()

            # Пропускаем слова, состоящие только из цифр и дефисов
            if re.match(r'^[\d\-]+$', word):
                continue
            if re.match(r'[a-zA-Z]', word):
                continue

            words.append((word.lower(), line_num, start_col,
                          start_global, end_global))

        current_global_pos += len(line) + 1  # +1 для символа новой строки

    return words


def generate_code_quality_report(critical_words: List[dict], file_path: str, original_text: str):
    """
    Генерирует отчет в формате GitLab Code Quality с точными позициями ошибок
    """
    report = {
        "version": "2.1",
        "issues": []
    }

    for i, error in enumerate(critical_words):
        # Получаем контекст строки для лучшего отображения в GitLab
        lines = original_text.split('\n')
        error_line = lines[error['line'] -
                           1] if error['line'] - 1 < len(lines) else ""

        # print(exception_dict)
        if check_with_exceptions(error['word']):
            seve = 'info'
            des = f"Spelling error: '{error['word']}' not found in dictionary, but naiden in slowar prepodavateleu"
        else:
            seve = 'major'
            des = f"Spelling error: '{error['word']}' not found in dictionary"

        issue = {
            "type": "issue",
            "check_name": "spelling",
            "description": des,
            "categories": ["Style"],
            "severity": seve,
            "location": {
                "path": file_path,
                "lines": {
                    "begin": error['line'],
                    "end": error['line']
                },
                "positions": {
                    "begin": {
                        "line": error['line'],
                        "column": error['column']
                    },
                    "end": {
                        "line": error['line'],
                        "column": error['column'] + len(error['word'])
                    }
                }
            },
            "fingerprint": f"spelling_error_{error['word']}_{error['line']}_{error['column']}_{i}"
        }
        report["issues"].append(issue)

    # Сохраняем отчет в файл
    output_file = "gl-spelling-report.json"
    # with open(output_file, 'w', encoding='utf-8') as f:
    #    json.dump(report, f, indent=2, ensure_ascii=False)

    # print(f"✓ Code Quality report saved to: {output_file}")
    print(json.dumps(report["issues"], indent=2, ensure_ascii=False))
    # Дополнительно сохраняем человеко-читаемый отчет
    #save_human_readable_report(critical_words, file_path)


def save_human_readable_report(critical_words: List[dict], file_path: str):
    """
    Сохраняет человеко-читаемый отчет с позициями ошибок
    """
    human_report = f"""# Spelling Analysis Report
File: {file_path}
Total errors: {len(critical_words)}
Critical errors: {len(critical_words)}

## Errors:
"""

    for error in critical_words:
        human_report += f"- '{error['word']}' at line {error['line']}, column {error['column']}\n"

    with open("spelling_report.txt", 'w', encoding='utf-8') as f:
        f.write(human_report)

    #print("✓ Human-readable report saved to: spelling_report.txt")


def main():
    if len(sys.argv) < 3:
        print("Usage: python spell_checker.py <input_file> [dictionary_path]")
        print("Example: python spell_checker.py document.txt /path/to/dictionaries/")
        sys.exit(1)

    input_file = sys.argv[1]
    dictionary_path = sys.argv[2] if len(sys.argv) > 2 else None

    dict2 = sys.argv[3]

    analyze_spelling(input_file, dictionary_path, dict2)


if __name__ == "__main__":
    main()

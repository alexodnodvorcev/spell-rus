#!/bin/bash
# (c) Alexander Kostritsky 2024
# Zhuleek ne worui
# Nu ladno worui

# Скрипт для поиска всех .tex файлов и запуска проверки
# Сохраняет результат в единый JSON файл

# Проверяем аргументы
if [ $# -eq 0 ]; then
    ROOT_DIR="."
    OUTPUT_FILE="gl-spelling-quality-report.json"
elif [ $# -eq 1 ]; then
    ROOT_DIR="$1"
    OUTPUT_FILE="gl-spelling-quality-report.json"
else
    ROOT_DIR="$1"
    OUTPUT_FILE="$2"
fi

# Проверяем существование директории
if [ ! -d "$ROOT_DIR" ]; then
    echo "Error: Directory '$ROOT_DIR' not found"
    exit 1
fi

# Временный файл для сбора результатов
TEMP_FILE=$(mktemp)

echo "Searching for .tex files in: $ROOT_DIR"

export PYTHONUTF8=1

# Находим все .tex файлы и обрабатываем их
find "$ROOT_DIR" -name "*.tex" -o -name "*.typ" -type f | while read -r tex_file; do
    echo "Processing: $tex_file"

    # Запускаем Python скрипт для каждого файла и добавляем результат во временный файл
    python spell-check.py "$tex_file" ./dicts/dict_pack_ru-aot-0.4.5.oxt ./dicts/iu7.txt | jq -c '.[]' >>"$TEMP_FILE"
done

# Собираем все результаты в один JSON массив
echo "[" >"$OUTPUT_FILE"
cat "$TEMP_FILE" | sed '$!s/$/,/' >>"$OUTPUT_FILE"
echo "]" >>"$OUTPUT_FILE"

# Удаляем временный файл
rm "$TEMP_FILE"

echo "Done! Results saved to: $OUTPUT_FILE"

echo "Total issues found: $(jq 'map(select(.severity != "info")) | length' "$OUTPUT_FILE")"

echo "Total slova iu7 found: $(jq 'map(select(.severity == "info")) | length' "$OUTPUT_FILE")"

#
if [ $(jq 'map(select(.severity != "info")) | length' "$OUTPUT_FILE") -ge 10 ]; then
    exit 1
fi

if [ $(jq 'map(select(.severity != "info")) | length' "$OUTPUT_FILE") -gt 0 ]; then
    exit 66
fi

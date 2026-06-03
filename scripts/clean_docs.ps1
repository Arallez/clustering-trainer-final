$docs = "d:\JetBrains\diploma-clustering-app\docs"
$commission = "$docs\commission"
$assets = "$docs\assets"

# Сначала создаем нужные папки
New-Item -Path $commission -ItemType Directory -Force | Out-Null
New-Item -Path $assets -ItemType Directory -Force | Out-Null

# Переносим документы для комиссии в отдельную папку
Move-Item -Path "$docs\*Руководство_оператора.docx" -Destination $commission -Force -ErrorAction SilentlyContinue
Move-Item -Path "$docs\*Техническое задание*.docx" -Destination $commission -Force -ErrorAction SilentlyContinue
Move-Item -Path "$docs\presentation_predefense_v4.pptx" -Destination $commission -Force -ErrorAction SilentlyContinue
Move-Item -Path "$docs\*Речь_защита*.md" -Destination $commission -Force -ErrorAction SilentlyContinue

# Удаляем мусор, старые версии, черновики и скрипты из docs
$deleteFiles = @(
    "presentation_predefense.pptx",
    "presentation_predefense_clean.pptx",
    "presentation_predefense_v2.pptx",
    "presentation_predefense_v2_clean.pptx",
    "presentation_predefense_v3.pptx",
    "build_conference_article.py",
    "check_algo_descriptions.py",
    "check_owl_descriptions.py",
    "check_owl_short_320.py",
    "db_schema_inspectdb_2026_05_05.py",
    "extract_current_diploma.py",
    "extract_pdf_tmp.py",
    "diploma_current_extract_2026_05_08.txt",
    "vkr_recommendations_2026_extract.txt",
    "tz_dump.txt",
    "db_schema_appendix_full.dot",
    "db_schema_appendix_full.png",
    "db_schema_full_all.dot",
    "db_schema_full_all_updated.dot",
    "db_schema_full_updated.dot",
    "db_schema_full_updated.png",
    "db_schema_generated_2026_05_05.dot",
    "db_schema_migrations_sql_2026_05_05.sql",
    "db_schema_plain.dot",
    "db_schema_project.dot",
    "db_schema_project_bw.dot",
    "article_example.docx",
    "article_interactive_clustering_manual.docx",
    "conference_article.docx"
)

foreach ($file in $deleteFiles) {
    Remove-Item "$docs\$file" -Force -ErrorAction SilentlyContinue
}

# Все оставшиеся картинки и диаграммы (svg, png, puml) перекидываем в assets
Move-Item -Path "$docs\*.png" -Destination $assets -Force -ErrorAction SilentlyContinue
Move-Item -Path "$docs\*.svg" -Destination $assets -Force -ErrorAction SilentlyContinue
Move-Item -Path "$docs\*.puml" -Destination $assets -Force -ErrorAction SilentlyContinue

Write-Output "Cleanup finished successfully."

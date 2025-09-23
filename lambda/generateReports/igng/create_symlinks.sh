rm -rf *.pdf

for file in ../../../../clinical_reports/igng/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

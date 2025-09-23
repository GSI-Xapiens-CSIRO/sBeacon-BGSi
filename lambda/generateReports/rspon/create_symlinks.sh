rm -rf *.pdf

for file in ../../../../clinical_reports/rspon/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

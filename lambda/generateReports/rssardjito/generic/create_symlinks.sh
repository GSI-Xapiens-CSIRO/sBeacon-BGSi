rm -rf *.pdf

for file in ../../../../../clinical_reports/rssardjito/gen/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

rm -rf *.pdf

for file in ../../../../../clinical_reports/rssardjito/crd/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

rm -rf *.pdf

for file in ../../../../../clinical_reports/rssardjito/md/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

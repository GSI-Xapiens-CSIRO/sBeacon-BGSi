rm -rf *.pdf

for file in ../../../../clinical_reports/rsjpd/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

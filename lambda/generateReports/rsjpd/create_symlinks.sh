rm -f *.pdf

for file in ../../../../report_templates/rsjpd/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

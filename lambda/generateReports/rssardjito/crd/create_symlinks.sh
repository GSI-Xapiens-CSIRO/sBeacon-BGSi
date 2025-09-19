rm -f *.pdf

for file in ../../../../../report_templates/rssardjito/crd/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

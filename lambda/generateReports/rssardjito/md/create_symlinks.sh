rm -f *.pdf

for file in ../../../../../report_templates/rssardjito/md/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

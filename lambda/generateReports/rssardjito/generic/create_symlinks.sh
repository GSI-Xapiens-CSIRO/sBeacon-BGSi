for file in ../../../../../report_templates/rssardjito/gen/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

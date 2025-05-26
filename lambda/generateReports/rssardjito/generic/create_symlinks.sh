for file in ../../../../../report_templates/rssardjito/gen/*.pdf; do
  cp "$file" "$(basename "$file")"
done

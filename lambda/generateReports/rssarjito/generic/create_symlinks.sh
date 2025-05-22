for file in ../../../../../report_templates/rssarjito/gen/*.pdf; do
  cp "$file" "$(basename "$file")"
done

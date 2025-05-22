for file in ../../../../../report_templates/rssarjito/gen/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

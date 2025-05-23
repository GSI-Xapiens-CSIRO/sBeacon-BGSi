for file in ../../../../../report_templates/rssarjito/md/*.pdf; do
  cp "$file" "$(basename "$file")"
done

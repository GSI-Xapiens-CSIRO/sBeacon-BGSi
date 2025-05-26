for file in ../../../../../report_templates/rssardjito/md/*.pdf; do
  cp "$file" "$(basename "$file")"
done

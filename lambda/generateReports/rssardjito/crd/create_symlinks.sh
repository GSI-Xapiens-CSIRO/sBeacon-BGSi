for file in ../../../../../report_templates/rssardjito/crd/*.pdf; do
  cp "$file" "$(basename "$file")"
done

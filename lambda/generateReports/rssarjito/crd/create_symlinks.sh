for file in ../../../../../report_templates/rssarjito/crd/*.pdf; do
  cp "$file" "$(basename "$file")"
done

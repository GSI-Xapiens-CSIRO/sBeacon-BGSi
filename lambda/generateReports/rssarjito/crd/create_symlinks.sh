for file in ../../../../../report_templates/rssarjito/crd/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

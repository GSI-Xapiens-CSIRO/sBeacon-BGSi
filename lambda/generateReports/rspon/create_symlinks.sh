for file in ../../../../report_templates/rspon/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

for file in ../../../../report_templates/rspon/*.pdf; do
  cp "$file" "$(basename "$file")"
done

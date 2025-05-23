for file in ../../../../report_templates/rsjpd/*.pdf; do
  cp "$file" "$(basename "$file")"
done

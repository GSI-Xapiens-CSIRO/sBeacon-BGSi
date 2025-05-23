for file in ../../../../report_templates/igng/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

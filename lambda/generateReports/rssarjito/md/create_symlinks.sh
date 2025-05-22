for file in ../../../../../report_templates/rssarjito/md/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

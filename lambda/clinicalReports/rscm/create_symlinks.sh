for file in ../../../../report_templates/html/rscm/*.html; do
  ln -s "$file" "$(basename "$file")"
done

for file in ../../../../report_templates/rscm/*.pdf; do
  cp "$file" "$(basename "$file")"
done

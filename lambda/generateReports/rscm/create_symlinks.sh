rm -f *.pdf

for file in ../../../../report_templates/rscm/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

rm -rf *.pdf

for file in ../../../../clinical_reports/rscm/*.pdf; do
  ln -s "$file" "$(basename "$file")"
done

#!/bin/sh
awk '
  BEGIN {FS="\t"}
  /Gene/ {next}
  ($3~/g/) {c=1}
  ($3~/mg/) {c=1e-3}
  ($3~/ug/) {c=1e-6}
  ($3~/ng/) {c=1e-9}
  ($3~/pg/) {c=1e-12}
  ($3~/fg/) {c=1e-15}
  {sub(" .*g/L", "", $3)}
  {AB[$1]=AB[$1]+c*$3; N[$1]++}
  END {printf("Gene Name\tConcentration in g/L\n"); for(a in AB) printf("%s\t%2.15f\n", a, AB[a]/N[a])}
' human_plasma_proteins_AB.tsv human_plasma_proteins_MS.tsv

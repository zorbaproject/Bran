#!/bin/bash

nvdb=$1

vdb80=$2

if [ -z $nvdb ] || [ -z $vdb80  ] ; then
echo "Esempio: ./compara.sh nuovovocabolariodibase.csv  vdb1980.csv"
exit 0
fi

#preparo due elenchi semplici di parole
cut -d ',' -f2 "$nvdb"  > "nvdb.txt"
sed -i "s/[0123456789]*//g" "nvdb.txt"
cut -d ',' -f2 "$vdb80" > "vdb80.txt"
sed -i "s/[0123456789]*//g" "vdb80.txt"
sed -i "s/.*;.*//g" "nvdb.txt"
sed -i "s/.*;.*//g" "vdb80.txt"

sort <"nvdb.txt" >"nvdb.txt.sorted"
sort <"vdb80.txt" >"vdb80.txt.sorted"
mv "nvdb.txt.sorted" "nvdb.txt"
mv "vdb80.txt.sorted" "vdb80.txt"

myreport="Ecco una statistica:"
myreport=$myreport$(echo "\nParole che esistono solo nel Nuovo Vocabolario di Base\n")
myreport=$myreport$(comm -23 "nvdb.txt" "vdb80.txt" | wc -l)

myreport=$myreport$(echo "\nParole che esistono solo nel vecchio Vocabolario di Base 1980\n")
myreport=$myreport$(comm -13 "nvdb.txt" "vdb80.txt" | wc -l)

myreport=$myreport$(echo "\nParole che esistono sia nell'edizione 1980 che in quella del 2016\n")
myreport=$myreport$(comm -12 "nvdb.txt" "vdb80.txt" | wc -l)

echo -e $myreport

myreport=$myreport$(echo "\n\nEcco gli elenchi completi:\n")

myreport=$myreport$(echo "\nParole che esistono solo nel Nuovo Vocabolario di Base\n")
myreport=$myreport$(comm -23 "nvdb.txt" "vdb80.txt")

myreport=$myreport$(echo "\nParole che esistono solo nel vecchio Vocabolario di Base 1980\n")
myreport=$myreport$(comm -13 "nvdb.txt" "vdb80.txt")

myreport=$myreport$(echo "\nParole che esistono sia nell'edizione 1980 che in quella del 2016\n")
myreport=$myreport$(comm -12 "nvdb.txt" "vdb80.txt")

echo -e $myreport > "comparazione.txt"

mv "nvdb.txt" "vdb2016.txt"
mv "vdb80.txt" "vdb1980.txt"

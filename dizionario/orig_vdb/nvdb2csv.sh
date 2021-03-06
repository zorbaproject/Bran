#!/bin/bash
#fonte: https://www.internazionale.it/opinione/tullio-de-mauro/2016/12/23/il-nuovo-vocabolario-di-base-della-lingua-italiana

mypdf=$1

if [ -z $mypdf ] ; then
echo "Esempio: ./nvdb2csv.sh nuovovocabolariodibase.pdf"
exit 0
fi

myfile=${mypdf//.pdf/}
echo "$myfile".html

pdftohtml "$mypdf" "$myfile".html
rm "$myfile".html
rm "$myfile"_ind.html

#sostituisco tutti gli spazi, carattere html &#160;
sed -i "s/&#160;/ /g" "$myfile"s.html

#seleziono solo il body
sed -n "/<body>/,/<\/body>/p" "$myfile"s.html > "$myfile".html
rm "$myfile"s.html
mv "$myfile".html "$myfile"s.html

#rimuovo il newline
cat "$myfile"s.html | tr -d '\n' > "$myfile".html 
rm "$myfile"s.html
mv "$myfile".html "$myfile"s.html

#rimuovo le iniziali
sed -i "s/<b>[QWERTYUIOPASDFGHJKLZXCVBNM]<\/b><br\/>/, /g" "$myfile"s.html

#rimuovo le interruzioni di pagina
newpage='dizionario.internazionale.it\/nuovovocabolariodibase<br\/>[0123456789]*<br\/><hr\/><a name=[0123456789]*><\/a>23 dicembre 2016<br\/>Il Nuovo vocabolario di base della lingua italiana - Tullio De Mauro - Internazionale<br\/>'
sed -i "s/${newpage}//g" "$myfile"s.html

#tutto in minuscole
sed -i 's/.*/\L&/g' "$myfile"s.html

#unisco le parole spezzate
sed -i "s/-<br\/>//g" "$myfile"s.html
sed -i "s/-<\/b><br\/><b>//g" "$myfile"s.html
sed -i "s/-<\/i><br\/><i>//g" "$myfile"s.html
sed -i "s/\([rtpsfglzcvbnm]\) \([aeiouèéòàùì]\)/\1\1\2/g" "$myfile"s.html

cp "$myfile"s.html "$myfile"TMP.html

#creo la divisione in righe
sed -i "s/<br\/>//g" "$myfile"s.html
sed -i "s/, \([qwertyuiopasdfghjklzxcvbnm\.1234567890]*\)\./; \1\./g" "$myfile"s.html
sed -i "s/,/\n/g" "$myfile"s.html 

#pulisco intestazione e pie di pagina
sed -i "s/<body>.*23 dicembre 2016/ /g" "$myfile"s.html 
sed -i "s/dizionario.internazionale.it\/nuovovocabolariodibase[0123456789]*<hr\/><\/body>//g" "$myfile"s.html

#creo la divisione in colonne
sed -i "s/  / /g" "$myfile"s.html 
sed -i "s/ /,/g" "$myfile"s.html
sed -i "s/,e,/;/g" "$myfile"s.html
sed -i "s/;,/;/g" "$myfile"s.html
sed -i "s/,di,prima,pers/ di prima pers/g" "$myfile"s.html
sed -i "s/,di,seconda,pers/ di seconda pers/g" "$myfile"s.html
sed -i "s/,di,terza,pers/ di terza pers/g" "$myfile"s.html
sed -i "s/,di,comando/ di comando/g" "$myfile"s.html
sed -i "s/s\.f\.,pl\./s\.f\. pl\./g" "$myfile"s.html
sed -i "s/m\.,inv/m\. inv/g" "$myfile"s.html


#aggiungo la colonna per bold-italic
sed -i "s/<\/i>//g" "$myfile"s.html
sed -i "s/<\/b>//g" "$myfile"s.html
sed -i "s/^\([^,]\)/,\1/g" "$myfile"s.html
sed -i "s/^/n/g" "$myfile"s.html
sed -i "s/n,<i>/i,/g" "$myfile"s.html
sed -i "s/n,<b>/b,/g" "$myfile"s.html
sed -i "s/\([nib]\),,/\1,/g" "$myfile"s.html

#TODO: si può eliminare la prima riga n

mv "$myfile"s.html "$myfile".csv
mv "$myfile"TMP.html "$myfile".html
echo "NOTA: il separatore delle colonne è ,"

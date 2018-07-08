#!/bin/bash
#fonte http://www.ctslaspezia.eu/wp-content/uploads/2017/04/GuidaUsoParole.pdf
mypdf=$1

if [ -z $mypdf ] ; then
echo "Esempio: ./vdb2csv.sh GuidaUsoParole.pdf"
exit 0
fi

myfile="vdb1980"

pdftohtml -i -f 152 -l 172 "$mypdf" "$myfile".html #ignoro immagini, solo pagine da 152 a 172
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
sed -i "s/<b>[QWERTYUIOPASDFGHJKLZXCVBNM] <\/b><br\/>/ /g" "$myfile"s.html

#rimuovo le interruzioni di pagina
newpage='<br\/>[0123456789]* <br\/><hr\/><a name=[0123456789]*><\/a>'
sed -i "s/${newpage}//g" "$myfile"s.html

#tutto in minuscole
sed -i 's/.*/\L&/g' "$myfile"s.html

#rimuovo i sinonimi
sed -i "s/\(“[qwertyuiopasdfghjklzxcvbnm]*”\)//g" "$myfile"s.html

cp "$myfile"s.html "$myfile"TMP.html

#pulisco intestazione e pie di pagina
sed -i "s/<body>.*riflessioni\./ /g" "$myfile"s.html 
sed -i "s/[0123456789]* <br\/><hr\/>.*<\/body>//g" "$myfile"s.html


#creo la divisione in righe
sed -i "s/<br\/>//g" "$myfile"s.html

sed -i "s/ *(/,/g" "$myfile"s.html
sed -i "s/)//g" "$myfile"s.html
sed -i "s/  / /g" "$myfile"s.html
sed -i "s/ <\/i>/<\/i> /g" "$myfile"s.html
sed -i "s/ <\/b>/<\/b> /g" "$myfile"s.html
sed -i "s/  / /g" "$myfile"s.html

#in ogni i e b tag non possono esserci due parole
check="0"
while [ $check -lt 1 ]
do
sed -i "s/\(<i>[qwertyuiopasdfghjklzxcvbnm]*\) /\1<\/i> <i>/g" "$myfile"s.html #\1 rappresenta il gruppo tra parentesi tonde, che quindi viene ricopiato tale e quale mentre lo spazio successivo non verrà copiato
if grep -q "<i>[qwertyuiopasdfghjklzxcvbnm]* " "$myfile"s.html; then
check="0"
else
check="1"
fi
done

check="0"
while [ $check -lt 1 ]
do
sed -i "s/\(<b>[qwertyuiopasdfghjklzxcvbnm]*\) /\1<\/b> <b>/g" "$myfile"s.html
if grep -q "<b>[qwertyuiopasdfghjklzxcvbnm]* " "$myfile"s.html; then
check="0"
else
check="1"
fi
done

sed -i "s/<b><\/b>//g" "$myfile"s.html 
sed -i "s/<i><\/i>//g" "$myfile"s.html 

sed -i "s/ /\n/g" "$myfile"s.html 


#creo la divisione in colonne
sed -i "s/\([^<]\)\//\1;/g" "$myfile"s.html

#aggiungo la colonna per bold-italic
sed -i "s/<\/i>//g" "$myfile"s.html
sed -i "s/<\/b>//g" "$myfile"s.html
sed -i "s/^/n,/g" "$myfile"s.html
sed -i "s/[qwertyuiopasdfghjklzxcvbnm],<i>/i,/g" "$myfile"s.html
sed -i "s/[qwertyuiopasdfghjklzxcvbnm],<b>/b,/g" "$myfile"s.html
sed -i "s/[qwertyuiopasdfghjklzxcvbnm],<i>/i,/g" "$myfile"s.html
sed -i "s/[qwertyuiopasdfghjklzxcvbnm],<b>/b,/g" "$myfile"s.html
sed -i "s/[qwertyuiopasdfghjklzxcvbnm],\([qwertyuiopasdfghjklzxcvbnm]*\)<\([ib]\)>/\2,\1/g" "$myfile"s.html #correggiamo la formattazione interna alle parole, tipo "n,a<i>mmuffire"


mv "$myfile"s.html "$myfile".csv
mv "$myfile"TMP.html "$myfile".html
echo "NOTA: il separatore delle colonne è ,"

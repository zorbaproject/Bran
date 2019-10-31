# Bran
Bran è un programma per la linguistica dei corpora. Nasce come soluzione completa per chi studia linguistica italiana creando e analizzando corpora di testi.
Il nome "bran" in lingua inglese indica la crusca, ed è un riferimento all'Accademia della Crusca.
![Logo di Bran](https://raw.githubusercontent.com/zorbaproject/VdB-Hacking/master/bran-logo-small.png)
ATTENZIONE: Al momento il repository di Bran contiene codice instabile. Per provare Bran, l'ultima release prima della riscrittura del codice è la 0.5 (https://github.com/zorbaproject/Bran/releases/tag/v0.5).

## Come funziona Bran
Bran utilizza le librerie grafiche PySide2 per disegnare una interfaccia grafica comoda. Inoltre, utilizza Tint, la versione italiana di StanfordCoreNLP per ottenere lemmatizzazione e PoS tagging dei testi, al posto dell'ormai inaffidabile treetagger. È stato testato su Windows (7-10) e GNU/Linux (Kubuntu). L'unico requisito per far funzionare Bran è Python3.6 a 64bit, poi basta lanciare lo script *main.py*. Al primo avvio, il programma installa tutte le librerie di cui ha bisogno. 
Per avere Python3 su un sistema Ubuntu si danno i comandi:
```
sudo apt-get install python3-pip
sudo apt-get install python3-tk
sudo apt-get install libxml2-dev libxslt1-dev python-dev
```

Su Windows è necessario installare Python3 (https://www.python.org/ftp/python/3.7.2/python-3.7.2-amd64.exe) e OpenJRE 10 (https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_windows-x64_bin.zip). È utile aggiungere Python alla PATH di Windows durante l'installazione.

Il classico workflow è il seguente: 
- Si avvia Bran, non si crea alcuna sessione di lavoro, si avvia Tint. Si chiude l'interfaccia grafica lasciando attivo solo il terminale. 
- Si avvia di nuovo Bran, stavolta creando una nuova sessione di lavoro (o aprendo una esistente).
- Si importa un file TXT, attendendo che venga integrato nella tabella del corpus
- A questo punto si possono eseguire le varie analisi disponibili nel menù

## Indicazioni per URL2Corpus
Nel menù *Strumenti* è presente un tool per il download di testi dal web. Questo può essere utilizzato per crearsi dei corpora da analizzare in seguito partento da blog, giornali online, e social networks. In particolare, per il sito di Repubblica e per l'Ansa, lo script cerca di riconoscere le porzioni di articolo in ogni pagina sulla base dei tag HTML. In altri casi, considera un paragrafo accettabile soltanto se al suo interno è presente almeno una parola del VdB 2016.
È anche possibile fornire come URL l'indirizzo di un feed RSS (es: http://www.repubblica.it/rss/cronaca/rss2.0.xml).
I testi ottenuti tramite questo strumento possono essere usati soltanto ai fini di ricerca accademica, senza scopi commerciali.

Esistono degli esempi del risultato di questo script all'indirizzo https://mega.nz/#F!aMozlbZb!RbQO7OrAFESvd6zmckgEGA

## Come aprire i file su Windows
Probabilmente l'idea migliore è utilizzare il programma Notepad++. Per farla breve, c'è un problema riguardo i caratteri "nuova riga", perché Windows non supporta lo standard "\n". Quindi Blocco Note non riesce a distinguere le righe, e diventa tutto illeggibile. Notepad++ funziona molto meglio (e ha un sacco di altre funzioni utili).
Notepad++ si trova qui:
https://notepad-plus-plus.org/repository/7.x/7.5.1/npp.7.5.1.Installer.exe
Ne esistono anche versioni "portable", per computer su cui non puoi installare programmi.
Per quanto riguarda la produzione di grafici, è necessario l'interprete R: https://cran.r-project.org/bin/windows/

## Crediti
- Tullio De Mauro ha scritto le varie edizioni originali del Vocabolario di Base
- Palmero Aprosio A. e Moretti G. hanno sviluppato Tint, un fork italiano di StanfordCoreNLP
- Floriana Sciumbata ha progettato le varie funzioni di Bran
- Luca Tringali ha scritto il codice di Bran

Se utilizzi Bran per una pubblicazione accademica, ti chiediamo di citarlo così:
```
{Bran, Floriana Sciumbata, Università di Udine}
{Italy goes to Stanford: a collection of CoreNLP modules for Italian}, {{Palmero Aprosio}, A. and {Moretti}, G., Fondazione Bruno Kessler Trento}
```
Il codice è pubblicato sotto licenza GNU GPL3, chiunque è invogliato a modificarlo e utilizzarlo, anche per scopi commerciali, a condizione di citare tutti gli autori e ripubblicare il codice.


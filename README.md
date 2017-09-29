# VdB Hacking
Proviamo a tradurre il Vocabolario di Base di De Mauro in un formato utilizzabile in programmi e analisi statistiche per i linguisti italiani.

## Come aprire i file su Windows
Probabilmente l'idea migliore è utilizzare il programma Notepad++. Per farla breve, c'è un problema riguardo i caratteri "nuova riga", perché Windows non supporta lo standard "\n". Quindi Blocco Note non riesce a distinguere le righe, e diventa tutto illeggibile. Notepad++ funziona molto meglio (e ha un sacoc di altre funzioni utili).
Notepad++ si trova qui:
https://notepad-plus-plus.org/repository/7.x/7.5.1/npp.7.5.1.Installer.exe
Ne esistono anche versioni "portable", per computer su cui non puoi installare programmi.
Per quanto riguarda la produzione di grafici, è necessario l'interprete R: https://cran.r-project.org/bin/windows/

## Cosa sono i vari file

- **nuovovocabolariodibase.pdf** è il file originale del nuovo vocabolario di base, ottenuto dall'indirizzo https://www.internazionale.it/opinione/tullio-de-mauro/2016/12/23/il-nuovo-vocabolario-di-base-della-lingua-italiana
- **GuidaUsoParole.pdf** è il file originale del testo di De Mauro del 1980, ottenuto dall'indirizzo http://www.ctslaspezia.eu/wp-content/uploads/2017/04/GuidaUsoParole.pdf
- **i file html** sono una versione HTML formattata e solo un po' ripulita dei due vocabolari di base
- **i file csv** sono delle tabelle che hanno tre colonne, separate dal simbolo virgola (cioè ,). La prima colonna contiene una n, una i, o una b, a seconda del fatto che nel vocabolario la parola fosse senza formattazione, in corsivo, o in grassetto. La seconda colonna contiene la parola stessa, mentre la terza colonna (facoltativa) contiene eventuali indicazioni grammaticali (es: aggettivo, sostantivo, etc...). Se una parola può avere più caratteristiche (per esmepio può essere sia un sostantivo che un aggettivo) le varie opzioni sono separate dal simbolo ;
- **i file nvdb2csv.sh e vdb2csv.sh** sono gli script bash (il terminale di GNU/Linux) utilizzati per tradurre i PDF nei CSV, è intuibile che nvdb2csv.sh si utilizzi per il nuovo vocabolario di base, mentre vdb2csv.sh si utilizzi per l'edizione 1980. Si tratta di una sequenza di regex, e ho aggiunto dei commenti in entrambi i file per provare a spiegarle. Comuqnue non è troppo complicato.
- **il file compara.sh** esegue una comparazione tra i due dizionari, per vedere quali parole siano cambiate tra il 1980 e il 2016
- **comparazione.txt** è il risultato dello script compara.sh, si tratta di un semplice report che mostra quante e quali parole siano presenti in uno solo dei due dizionari oppure in entrambi. Nei tre elenchi, le parole sono separate da uno spazio, se vuoi trasformarli in una tabella basta selezionarle e usare lo spazio come delimitatore di riga (o colonna).
- **vdb1980.txt e vdb2016.txt** sono le semplici liste dei vocaboli, senza altre informazioni, delle due versioni del vocabolario di base. Questi due file vengono prodotti automaticamente dallo script compara.sh e sono probabilmente il migliore punto di partenza per chi deve fare semplici analisi statistiche perché sono "puliti" e pronti all'uso
- **esempi** è la cartella che contiene dei programmi di esempio basati sui dataset prodotti

Una nota sugli script: se non sai quali argomenti fornire ad uno script, eseguirlo senza argomenti ti fornisce un suggerimento.

## Esempi
- **diagramma-di-venn.py** Produce del codice R che permette di disegnare un diagramma di Venn mostrando in quale VdB si trovi una certa parola

## Potenziali difetti (#TODO:)
- A causa dell'origine dei testi come PDF, è possibile che alcune cose non abbiano funzionato. Sarebbe opportuno controllare meglio che ogni parola sia riportata correttamente.
- Le due versioni del vocabolario usano due standard diversi per le indicazioni grammaticali. Per esempio, "aggettivo" diventa "agg.". Nel caso si voglia fare una comparazione, basta realizzare un semplice array di traduzione. Il fatto è che nell'edizione 1980 molte parole non hanno nemmeno una di queste indicazioni, quindi pare poco utile fare un confronto.
- Ci sono due sole versioni del VdB: potrebbe essere più interessante avere versioni intermedie per capire come sia cambiato il linguaggio nel corso del tempo

## Crediti
Tullio De Mauro ha scritto le varie edizioni originali del Vocabolario di Base
Floriana Sciumbata ha suggerito le applicazioni pratiche di un dataset basato sul VdB nella linguistica italiana
Luca Tringali ha scritto gli script che producono i dataset csv e txt

Il codice è pubblicato sotto licenza GNU GPL3, chiunque è invogliato a modificarlo e utilizzarlo, anche per scopi commerciali, a condizione di citare tutti gli autori e ripubblicare il codice. I PDF originali sono qui riportati solo per comodità, non sono da considerarsi inclusi nella licenza GPL3.

#!/usr/bin/Rscript

#Se lo script viene eseguito da amministratore (permessi di scrittura nella cartella delle librerie), installa le librerie
if (file.access(.libPaths()[1],2)==0) {
    install.packages("ggplot2",repos = "https://cran.stat.unipd.it/");
    install.packages("gridSVG",repos = "https://cran.stat.unipd.it/");
    print("Se ci sono stati errori, esegui sudo apt-get install libxml2-dev e riprova.")
    print("Sembra che tu sia amministratore, sarebbe meglio procedere solo da utente semplice. Vuoi comunque creare i grafici? [y/N]");
    choice <- readLines("stdin", 1);
    if (choice != "Y" && choice != "y") quit();
}

library(ggplot2);
require(gridSVG);


fullpath <- "mytable.csv";

file <- read.table(fullpath,header=TRUE, sep="\t", col.names=c("BranColonna0" , "BranColonna1", "BranColonna2"), colClasses = c("character", "numeric", "factor"));


for(i in levels(file$BranColonna2)){
    if (i != "") {
        basename <- sub('\\.csv$', '', fullpath);
        basename <- paste(basename,"-", i);

        mytb <- subset(file, file$BranColonna2==i & file$BranColonna1!="");
        mytb <- droplevels(mytb);
        #print(mytb);
        #print(levels(mytb));
        
        mytb$BranColonna0 <- factor(mytb$BranColonna0, levels = mytb$BranColonna0[order(mytb$BranColonna1)])

        # Scrivo i dati per debug
        print(basename)
        print(mytb);
        # Creo un istogramma
        histogram = ggplot(mytb, aes(x=mytb$BranColonna0, y=mytb$BranColonna1, fill=mytb$BranColonna0)) + geom_bar(stat="identity");
        # Percentuale o numero puro nelle etichette?
        mylabels = mytb$BranColonna1;
        histogram = histogram + stat_count(aes(y=..count..,label=mylabels),geom="text",vjust=-1)
        histogram = histogram + labs(x = NULL, y = NULL, fill = NULL, title = sub('-', ' ', basename));
        histogram = histogram + theme_classic() + theme(axis.line = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank(),
        plot.title = element_text(hjust = 0.5, color = "#666666"));

        #Esporto il grafico in un file SVG
        print(histogram);
        grid.export(paste(basename, ".svg", sep=""),addClasses=TRUE);
    }
}


#basename <- sub('\\.csv$', '', fullpath);
#file <- read.table(fullpath,header=TRUE, sep="\t", col.names=c("BranColonna0" , "BranColonna1"), colClasses = c("character", "numeric"));
# Ordino la tabella in base alla prima colonna (i punteggi calcolati con le risposte degli utenti)
#file <- file[order(file$BranColonna1),];

#Esporto il grafico in un file SVG
#print(histogram);
#grid.export(paste(basename, ".svg", sep=""),addClasses=TRUE);

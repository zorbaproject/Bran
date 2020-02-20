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

basename <- sub('\\.csv$', '', fullpath);
file <- read.table(fullpath,header=TRUE, sep="\t", col.names=c("BranColonna0"), colClasses = c("character"));
# Ordino la tabella in base alla prima colonna (i punteggi calcolati con le risposte degli utenti)
#file$BranColonna0 <- factor(file$BranColonna0, levels = file$BranColonna0[order(file$BranColonna1)])
# Scrivo i dati per debug
print(basename)
print(file);
# Creo un istogramma
histogram = ggplot(data.frame(file$BranColonna0), aes(x=file$BranColonna0, fill=file$BranColonna0)) + geom_histogram(position = "identity", stat="count", alpha = 1);
histogram = histogram + geom_text(stat = "count", aes(label = ..count.., y = ..count..));
histogram = histogram + labs(x = NULL, y = NULL, fill = NULL, title = sub('-', ' ', basename));
histogram = histogram + theme_classic() + theme(axis.line = element_blank(),
    axis.text = element_blank(),
    axis.ticks = element_blank(),
    plot.title = element_text(hjust = 0.5, color = "#666666"));
#Esporto il grafico in un file SVG
print(histogram);
grid.export(paste(basename, ".svg", sep=""),addClasses=TRUE);

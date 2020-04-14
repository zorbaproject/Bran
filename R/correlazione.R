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
library(gridSVG);


histogramsByGroup <- function(tmpname, mygrouptable, mygroup, mygroupid, mydatatable, mydata, mydataid, myregex = "", mycase = TRUE) {
    
    #tmpname è un testo col titolo del grafico
    
    tmptable <- data.frame(ID= character(), GROUP= factor(), DATA= factor());
    for(i in levels(mydatatable[[mydataid]])){
        # Note: we expect there is only one row for each table with the same ID
        grp <- mygrouptable[mygrouptable[[mygroupid]] == i, mygroup];
        if (is.null(grp) || length(grp)==0) grp <- "NULL";
        dt <- mydatatable[mydatatable[[mydataid]] == i, mydata];
        if (is.null(dt)) dt <- "NULL";
        print(i);
        print(grp);
        print(dt);
        tmptable <- rbind(tmptable, list(ID=i,GROUP=grp,DATA=dt));
    }
    names(tmptable) <- c(mydataid, mygroup, mydata);
    
    #print(tmptable);
    
    tmpgroup <- as.factor(tmptable[[mygroup]])
    tmpdata <- as.factor(tmptable[[mydata]])  #Note: [[]] returns a dataframe, while [] would return a vector
    
    if (myregex == "") {
        for(i in levels(tmpgroup)){
            if (i != "") {    
            if (mycase) {
                mytb <- subset(tmpdata, tmpgroup==i & tmpgroup!="");
            } else {
                mytb <- subset(tmpdata, tolower(tmpgroup)==tolower(i) & tmpgroup!="");
            }
            mytb <- droplevels(mytb);
            #print(mytb);
            print(levels(mytb));
                
            histogram = ggplot(data.frame(mytb), aes(x=mytb, fill=mytb)) + geom_histogram(position = "identity", stat="count", alpha = 1);
            histogram = histogram + geom_text(stat = "count", aes(label = ..count.., y = ..count..));
             
            histogram = histogram + labs(x = NULL, y = NULL, fill = NULL, title = sub('-', ' ', tmpname));
                
            histogram = histogram + theme_classic() + theme(axis.line = element_blank(),
                axis.text = element_blank(),
                axis.ticks = element_blank(),
                plot.title = element_text(hjust = 0.5, color = "#666666"));
                
            #Esporto il grafico in un file SVG
            print(histogram);
            grid.export(paste("./", tmpname, "-", sub('[^A-Za-z0-9]', '', i), ".svg", sep=""),addClasses=TRUE);
            }
        }
    } else {
        tmpcase <- !mycase;
        mytb <- subset(tmpdata, grepl(myregex, tmpgroup, perl=TRUE, ignore.case=tmpcase));
        mytb <- droplevels(mytb);
        #print(mytb);
        print(levels(mytb));
        
        histogram = ggplot(data.frame(mytb), aes(x=mytb, fill=mytb)) + geom_histogram(position = "identity", stat="count", alpha = 1);
        histogram = histogram + geom_text(stat = "count", aes(label = ..count.., y = ..count..));
        
        histogram = histogram + labs(x = NULL, y = NULL, fill = NULL, title = sub('-', ' ', tmpname));
        
        histogram = histogram + theme_classic() + theme(axis.line = element_blank(),
            axis.text = element_blank(),
            axis.ticks = element_blank(),
            plot.title = element_text(hjust = 0.5, color = "#666666"));
        
        #Esporto il grafico in un file SVG
        print(histogram);
        grid.export(paste("./", tmpname, "-", sub('[^A-Za-z0-9\\[\\]]', '_', myregex), ".svg", sep=""),addClasses=TRUE);
    }
    
}


histogramSorted <- function(tmpname, tmpdata) {
        #tmpname è il titolo del grafico
        #tmpdata è un dataframe con due sole colonne, la prima contiene le etichette e la seconda la dimensione delle barre degli istogrammi
    
        mytb <- data.frame(table(tmpdata))
        colnames(mytb) <- c("Dati","Freq")
        #mytb <- mytb[order(mytb$Freq),];
        mytb$Dati <- factor(mytb$Dati, levels = mytb$Dati[order(mytb$Freq)])
        print(mytb);
        
        histogram = ggplot(mytb, aes(x=Dati, y=Freq, fill=mytb$Dati )) + geom_bar(position = "identity", stat="identity", alpha = 1);

        histogram = histogram + geom_text(stat = "count", aes(label = mytb$Freq, y = ..count..));
        histogram = histogram + labs(x = NULL, y = NULL, fill = NULL, title = sub('-', ' ', tmpname));

        histogram = histogram + theme_classic() + theme(axis.line = element_blank(),
         axis.text = element_blank(),
         axis.ticks = element_blank(),
         plot.title = element_text(hjust = 0.5, color = "#666666"));

        #Esporto il grafico in un file SVG
        print(histogram);
        grid.export(paste("./", tmpname, ".svg", sep=""),addClasses=TRUE);

}

#Routine principale



#!/usr/bin/Rscript
install.packages("VennDiagram",repos = "https://cran.stat.unipd.it/");
require(VennDiagram);
x <- list();
x$VdB1980 <- as.character(c( "autobus", "autostop", "boxe", "cachet", "camion", "chic", "cognac", "collant", "garage", "mobile", "réclame", "roulotte", "taxi", "tic", "toilette", "no", "bar", "camera", "clacson", "clan", "data", "disco", "festival", "film", "future", "goal", "in", "media", "motel", "nylon", "pace", "pala", "plaid", "polo", "pullman", "pullover", "record", "shampoo", "sport", "stop", "tennis", "thermos", "toast", "tram", "tunnel", "whisky", "mite", "sci", "ananas", "da", "polo", "salsa", "torero", "stop", "alt", "lama", "mensa", ""));
x$VdB2016 <- as.character(c( "muta", "album", "autobus", "autostop", "brioche", "buffet", "camion", "casino", "collant", "crêpe", "dessert", "foulard", "garage", "hotel", "lingerie", "menu", "mobile", "mousse", "parquet", "peluche", "robot", "roulotte", "slip", "taxi", "tic", "toilette", "tour", "no", "baby", "band", "bar", "basket", "bikini", "bit", "blog", "boss", "box", "boxer", "brand", "business", "camera", "cardigan", "chat", "clacson", "clan", "club", "comfort", "community", "computer", "copyright", "cracker", "data", "design", "detective", "disco", "e-mail", "fan", "festival", "fiction", "file", "film", "flash", "forum", "gay", "goal", "gossip", "hamburger", "hobby", "home", "in", "internet", "jeans", "ketchup", "killer", "kit", "kiwi", "leader", "link", "live", "look", "manager", "marketing", "master", "media", "mister", "monitor", "motel", "network", "news", "nylon", "ok", "okay", "pace", "pala", "partner", "party", "picnic", "plaid", "poker", "polo", "pony", "premier", "privacy", "pub", "pullman", "pullover", "punk", "puzzle", "quiz", "record", "rock", "safari", "set", "sexy", "shampoo", "share", "shopping", "shorts", "show", "single", "sir", "slogan", "smog", "snack", "sneaker", "software", "sol", "spam", "sport", "spot", "spray", "standard", "star", "status", "stop", "stress", "tag", "team", "tennis", "test", "thermos", "toast", "top", "trend", "tunnel", "video", "wafer", "whisky", "sci", "ananas", "da", "vodka", "chat", "auto", "polo", "salsa", "sol", "torero", "stop", "boxer", "speck", "lama", "mensa", "yogurt", ""));
v0 <-venn.diagram(x, lwd = 3, col = c("red", "green"), fill = c("orange", "yellow"), apha = 0.5, filename = NULL, imagetype = "svg");
grid.draw(v0);
overlaps <- calculate.overlap(x);
base <- (length(x)*2);
vl <- 9; #length(v0)
for (i in 1:length(overlaps)){
if (i<base-1) {
v0[[vl-base+i-1]]$label <- paste(setdiff(overlaps[[base-1-i]], overlaps[[base-1]]), collapse = "\n");
} else {
v0[[vl-base+i-1]]$label <- paste(overlaps[[base-1]], collapse = "\n");
}
}
svg(filename = "diagrammavenn.svg");
grid.newpage();
grid.draw(v0);

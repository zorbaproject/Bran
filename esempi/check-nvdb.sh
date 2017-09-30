#!/bin/bash
cat ../nuovovocabolariodibase.csv | grep -v '^[inb],[0123456789qwertyuiopasdfghjklzxcvbnmèéòàìù-]*,[0123456789qwertyuiopasdfghjklzxcvbnm;\. ]*$'
# grep -v nega la regex

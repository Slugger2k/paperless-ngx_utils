#!/bin/bash

counter=2

while true; do
    echo "Starte Python-Skript mit Argument: $counter"
    python3 paperless_remove_duplicated_corespondents.py --limit 15 --page "$counter"
    counter=$((counter + 1))
    sleep 1  # optional: 1 Sekunde warten
done


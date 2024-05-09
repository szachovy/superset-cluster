#!/bin/bash

ft_local=$(awk '$1=="Local:" {flag=1} flag' <<< "$(</proc/net/fib_trie)")

for IF in $(ls /sys/class/net/); do
    networks=$(awk '$1=="'$IF'" && $3=="00000000" && $8!="FFFFFFFF" {printf $2 $8 "\n"}' <<< "$(</proc/net/route)" )
    for net_hex in $networks; do
            net_dec=$(awk '{gsub(/../, "0x& "); printf "%d.%d.%d.%d\n", $4, $3, $2, $1}' <<< $net_hex)
            mask_dec=$(awk '{gsub(/../, "0x& "); printf "%d.%d.%d.%d\n", $8, $7, $6, $5}' <<< $net_hex)
            awk '/'$net_dec'/{flag=1} /32 host/{flag=0} flag {a=$2} END {print "'$IF':\t" a "\n\t'$mask_dec'\n"}' <<< "$ft_local"
    done
done

exit 0
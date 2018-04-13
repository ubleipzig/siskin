#!/usr/bin/env python3
# coding: utf-8


# SID: 129
# Collection: geoscan
# refs: #9871


import io
import sys
import json
import marcx
import pymarc
import feedparser


def get_field(tag):  
    try:
        return record[tag]
    except:
        return ""


inputfilename, outputfilename = "129_input.xml", "129_output.mrc"

if len(sys.argv) == 3:
    inputfilename, outputfilename = sys.argv[1:]

outputfile = io.open(outputfilename, "wb")

records = feedparser.parse(inputfilename)

for record in records.entries:

    marcrecord = marcx.Record(force_utf8=True)
    marcrecord.strict = False

    # Leader
    marcrecord.leader = "     naa  22        4500"

    # Identifikator
    f001 = get_field("guid")
    marcrecord.add("001", data="finc-126-" + f001)
    
    # Format
    marcrecord.add("007", data="cr")

    # Sprache
    f041a = get_field("geoscan_language")
    if f041a == "English":
        f041a = "eng"
    elif f041a == "French":
        f041a = "fre"
    else:        
        print("Sprache ergänzen: " + f041a)
        f041a = "eng"
    marcrecord.add("041", a=f041a)

    # 1. Urheber
    f100a = get_field("geoscan_author")
    if ";" in f100a:
        f100a = f100a.split("; ")
        f100a = f100a[0]
    marcrecord.add("100", a=f100a)

    # Haupttitel    
    f245a = get_field("title")    
    marcrecord.add("245", a=f245a)

    # Verlag
    f260a = get_field("geoscan_publisher")    
    marcrecord.add("260", a=f260a)

    # Kurzreferat
    f520a = get_field("geoscan_abstract")
    marcrecord.add("520", a=f520a)

    # weitere Urheber
    f700a = get_field("geoscan_author")
    if ";" in f700a:
        authors = f700a.split("; ")
        for f700a in authors[1:]:
            marcrecord.add("700", a=f700a)

    # URL
    f856u = get_field("link")
    marcrecord.add("856", q="text/html", _3="Link zur Ressource", u=f856u)
    
    # 980
    collections = ["a", f001, "b", "129", "c", "geoscan"]
    marcrecord.add("980", subfields=collections)
   
    outputfile.write(marcrecord.as_marc())

outputfile.close()
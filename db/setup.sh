#!/bin/bash

mypath=`realpath "$0"`
mybase=`dirname "$mypath"`
cd $mybase

datadir="${1:-data/}"
if [ ! -d $datadir ] ; then
    echo "$datadir does not exist under $mybase"
    exit 1
fi

source ../.flaskenv
dbname=$DB_NAME

if [[ -n `psql -qtc "SELECT datname FROM pg_database" | cut -d \| -f 1 | grep -w "$dbname"` ]]; then
    psql -c "DROP DATABASE $dbname"
fi
psql -c "CREATE DATABASE $dbname"

psql -af create.sql $dbname
cd $datadir
psql -af $mybase/load.sql $dbname
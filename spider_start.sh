#!/bin/sh

base=$(cd "$(dirname "$0")"; pwd)
cd $base

#nohup scrapy crawl myspider -a term='hotel' -a location='los angeles ca' > ./logs/my.log 2>&1 &
nohup scrapy crawl yellowpagespider> ./logs/yellowpage.log 2>&1 &

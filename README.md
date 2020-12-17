# hb_scraper
## A collection of utilities for taking an iterative backup of the halfbakery
## and enabling analysis of captured content. 

### 17th December 2020
Currently residing in a jupyter notebook, some code covering the following functions exists:
1) Ping a search url and harvest a collection of links
2) Visit each link, and extract idea content, annotations and links
3) Compare downloaded content with content stored in a database to determine difference between "stale" and "fresh" content. Discard any "stale" content. 
4) Store fresh content in a form that enables onward analysis 


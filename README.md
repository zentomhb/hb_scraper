# hb_scraper
## A collection of utilities for taking an iterative backup of the halfbakery and enabling analysis of captured content.

See http://www.halfbakery.com/idea/F_fcrst_20annual_20HalfBakery_20_93Wo_20ist_20der_20F_fchrer_20_3f_94_20programming_20competition_2e#1608584088 for context.

### 30th December

  1.  Added searches for additional historical figures.
  
### 26th December

A series of edits including:

  1. fixes to perform commits, where previously the database was essentially had a single session lifespan.
  2. Inclusion of idea_title and idea_description into the searchable collection of user-contributions. (This fix prompted by Dub's BREXIT Whoopie Cushion idea that initially didn't trigger any update to the latest search)


### 21st December 2020
Now producing outputs to topic searches, still running within a jupyter notebook, only now referencing core utilities via calls to python imports.
Additional functionality added includes:

  1. Inbuilt database views to provide a unified "latest update" view across multiple fetches - bringing back only the latest version of each individual idea url content.
  2. A new view to present each user's contribution as a (near) chronologically accurate list of ideas, annos and links.  
  3. Ability to apply regex searches across this chronological dataset, and report the most recent time a particular match is found, and calculate the number of days since that event, and the current timestamp.

TODO:
  1. Push more of the jupyter hosted code down into appropriate python modules
  2. Develop the startup script a little so it can reliably seed a reasonably sized cache of reasonably recent content.
  3. Develop more command-line utility calls so simple calls can be made to perform scheduled tasks.

### 17th December 2020
Currently residing in a jupyter notebook, some code covering the following functions exists:
1) Ping a search url and harvest a collection of links
2) Visit each link, and extract idea content, annotations and links
3) Compare downloaded content with content stored in a database to determine difference between "stale" and "fresh" content. Discard any "stale" content.
4) Store fresh content in a form that enables onward analysis

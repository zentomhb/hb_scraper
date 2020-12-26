# Class used to interface with halfbakery
import requests, re, json, datetime
import os, sys
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
import uuid
from hashlib import md5
import dateparser
import sqlite3

import pandas as pd

def recombine_link_list(link_list):
    rlist = []
    t = ""
    s=-1
    for (url, text ,subtitle, desc, user, date ) in link_list:
        s = s + 1
        try:
            rlist.append((s, url, text, subtitle, desc, user, dateparser.parse(date).timestamp()))
        except:
            print ((s, url, text, subtitle, desc, user, dateparser.parse(date)))
            rlist.append((s, url, text, subtitle, desc, user, dateparser.parse(date)))
    return rlist

def recombine_anno_list(anno_list):
    rlist = []
    t = ""
    s=-1
    for (a,u,d) in anno_list:
        if u=="" and d=="":
            t=t+" "+a
        else:
            s=s+1
            t=(t+" "+a)
            #rlist.append((s,t.replace("\r\n", ""),u,d))
            rlist.append((s,t,u,dateparser.parse(d).timestamp()))
            t=""
    return rlist

def scrape_link_values(link_list_soup_element):
    link_url = link_list_soup_element.find('a')['href']
    link_attribution_regex = re.compile(r"\[(.*),\s([A-Z][a-z]{2}\s[\d]{1,2} [\d]{4})(?:\]|,\slast modified.*?])$")
    try:
        link_text = "".join(link_list_soup_element.find_next_sibling().find('nobr').strings)
    except:
        link_text = ""
    link_subtitle = "".join(link_list_soup_element.find('a').strings)


    try:
        link_desc = "".join("".join(link_list_soup_element.find_next_sibling().find('br').next_element))
    except TypeError:
        link_desc = "???"
    link_user = "".join(link_list_soup_element.find_next_sibling().find('a').strings)
    lstring = "".join(link_list_soup_element.find_next_sibling().strings)

    link_attribution_groups = link_attribution_regex.search("".join(link_list_soup_element.find_next_sibling().strings).strip())
    #print(link_attribution_groups)
    if link_attribution_groups is not None:
        #print(link_attribution_groups.group(1)==link_user, " user link ", link_user)
        link_date = link_attribution_groups.group(2)
    else:
        link_date = "".join(link_list_soup_element.find_next_sibling().strings)[lstring.find(link_user)+
                len(link_user)+2:lstring.find(']',lstring.find(link_user)+len(link_user))]
    try:
        link_date = datetime.strptime(
            re.search("([Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec]{3} \d{2} \d{4})", link_date).group(1), "%b %d %Y").isoformat()
    except:
        pass
        #print(link_date)
    if link_desc[-1:]=="[":
        link_desc=link_desc[:-1].strip()
    return link_url, link_text, link_subtitle, link_desc, link_user, link_date

def scrape_annotations(anno_element):
    #print(anno_element)
    anno_content = "".join(anno_element.find('font', attrs={'class':'fcs'}).strings)
    try:
        anno_user = "".join(anno_element.find('td', attrs={'class':'fcs'}).find('a').strings)
        #anno_date = datetime.datetime.now()
        anno_date = "".join(anno_element.find('td', attrs={'class':'fcs'}).strings)[-11:]
    except:
        anno_user = ""
        anno_date = ""
    return anno_content, anno_user, anno_date



def get_links(s, url):
    r = s.get (url)
    page_links_regex = re.compile("<a class=\"(?:newidea|oldidea)\" href=\"(/idea/.*?)\"")
    link_harvest = [urljoin(url,l).split("#")[0] for l in page_links_regex.findall(r.text)]
    return link_harvest


class IdeaPage():
    fetch_id=None
    url=None
    hash=None
    title=None
    description=None
    copy=None
    user=None
    idea_date=None
    links=None
    annos=None
    fetch_date=None
    update_since=None

    def __init__(self, hb_link, start_timestamp):
        l=hb_link
        self.url=l
        s = requests.Session()
        r = s.get(l)
        self.start_timestamp = start_timestamp
        self.fetch_date=datetime.datetime.now().timestamp()
        soup=bs(r.text,"html.parser")
        mainpanel = soup.find('td', attrs={'class':'mainpanel'})
        idea_header = mainpanel.findAll('table')[2]
        self.title = str("".join(idea_header.find('a', attrs={'name':'idea'}).strings))
        self.fetch_id = str(uuid.uuid4())
        self.description = "".join(mainpanel.find('font', attrs={'class':'fcl'}).strings)
        #votes = self.getvotes("".join(mainpanel.find('td', attrs={'class':'controls'}).find('td', attrs={'valign':'top', 'align':'center'}).strings).replace("(","").replace(")","").split(","))
        self.copy = str("".join(idea_header.find('div', attrs={'class':'copy'}).strings))
        (self.user, text_date) = ( n.strip() for n in str("".join(idea_header.find('td', attrs={'class':'fcm'}).strings)).split(","))
        #idate = datetime.datetime.strptime(text_date, "%b %d %Y").isoformat()
        self.idate=dateparser.parse(text_date).timestamp()
        self.links = recombine_link_list([scrape_link_values(n) for n in idea_header.findAll('font', attrs={'class':'fcm'})])
        self.annos = recombine_anno_list([scrape_annotations(n) for n in idea_header.next_siblings if n.name=='table'])
        #print("".join([str(j) for j in [title, description, copy, user, idate, links, annos]]).encode("utf-8"))
        self.hash = md5("".join([str(j) for j in [self.title, self.description, self.copy, self.user, self.idate, self.links, self.annos]]).encode("utf-8")).hexdigest()
        self.update_since = start_timestamp
        print (self.hash)

    def __repr__(self):
        return "<Class:IdeaPage:" + str(self.to_dict()) + ">"

    def to_dict(self):
        return {
                     "fetch_id" : self.fetch_id,
                     "url" : self.url,
                     "hash" : self.hash,
                     "title":self.title,
                     "description" : self.description,
                     "copy" : self.copy,
                     "user" : self.user,
                     "idea_date" : self.idate,
                     "links": self.links,
                     "annos" : self.annos,
                     "fetch_date" : self.fetch_date,
                     "update_since" : self.update_since
                }

class HarvestLinks():
    def __init__(self, search_links, start_timestamp):
        self.start_timestamp = start_timestamp
        s = requests.Session()
        contents = []

        for url in search_links:
            link_harvest=get_links(s, url)
            contents.extend(link_harvest)
        self.fetch_links=list(set(contents))


    def fetch_data(self):
        print("Processing...\n {l} pages to collect".format(l=len(self.fetch_links)))
        ping_n = 10
        contents=[]
        e=0
        for e,l in enumerate(self.fetch_links):
            contents.append(IdeaPage(l,self.start_timestamp))
            if (e+1) % ping_n == 0:
                print ("Read {e} of {l}...".format(e=e+1, l=len(self.fetch_links)))
        print( )
        if e > 0:
            print ("Complete read {e} of {l}".format(e=e+1, l=len(self.fetch_links)))

        self.lindex = [c.url for c in contents]
        self.contents=contents

class DataStore():
    def __init__(self, storage_db=None, trash=False):
        if storage_db is None:
            storage_db = "hb.db"
        self.connection = sqlite3.connect(storage_db)
        try:
            content_test = self.query_to_recordset("select count(*) count from idea_fetch")
            print ("idea count: {c}".format(c=content_test[0]["count"]))
        except:
            print("Idea-count failed.")
        # Test whether all the needed tables exist - if not, create a new schema:
        table_test = self.query_to_recordset("select tbl_name from sqlite_master")
        if table_test==[{'tbl_name': 'idea_fetch'},
                {'tbl_name': 'anno_fetch'},
                {'tbl_name': 'link_fetch'},
                {'tbl_name': 'fresh_ideas'},
                {'tbl_name': 'latest_user_content'}] and trash==False:
            # Expected content in the database - do nothing
            print("Database Schema Exists")

        else:
            if trash is not False:
                print("Building new schema any existing content will be lost.")
                self.sql_create_schema()
            else:
                print ("Schema change - please review the contents of your database - maybe a version mismatch")

    def __del__(self):
        print ("Closing Session")
        self.connection.close()

    def save_idea(self, idea, force_overwrite=False):
        c=self.connection.cursor()
        if not force_overwrite:
            test_content = self.query_to_recordset("select url, hash, fetch_id from fresh_ideas where url = ?", [idea.url])
            if len(test_content) > 0 and test_content[0]['hash']==idea.hash:
                print("Hashmatch - already cached")
                return None
            else:
                print("Saving.")

        c=self.connection.cursor()
        idea_insert_sql = """INSERT INTO idea_fetch VALUES
                            ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )"""
        anno_insert_sql = """INSERT INTO anno_fetch VALUES
                            ( ?, ?, ?, ?, ? )"""
        link_insert_sql = """INSERT INTO link_fetch VALUES
                        ( ?, ?, ?, ?, ?, ?, ?, ? )"""
        #links_pk = uuid.uuid4()
        #annos_pk = uuid.uuid4()
        idea_values = [idea.fetch_id,
                       idea.url,
                       idea.hash,
                       idea.title,
                       idea.description,
                       idea.copy,
                       idea.user,
                       idea.idate,
                       idea.fetch_date,
                       idea.update_since]
        #for e,v in enumerate(idea_values):
        #    print(e,v)
        c.execute(idea_insert_sql, idea_values)
        self.connection.commit()
        for anno in idea.annos:
            anno_values = [idea.fetch_id,
                           anno[0],
                           anno[1],
                           anno[2],
                           anno[3]]
            c.execute(anno_insert_sql, anno_values)
        self.connection.commit()
        for link in idea.links:
            link_values = [idea.fetch_id,
                           link[0],
                           link[1],
                           link[2],
                           link[3],
                           link[4],
                           link[5],
                           link[6]]
            c.execute(link_insert_sql, link_values)
        self.connection.commit()
        c.close()

    def query_to_recordset(self, query, parameters=None):
        c = self.connection.cursor()
        try:
            if parameters is not None:
                rs = c.execute(query, parameters)
            else:
                rs = c.execute(query)
        except sqlite3.OperationalError as err:
            return err
        schema = rs.description
        return_set = []
        for r in rs:
            return_set.append({schema[e][0]:r[e] for e in range(0,len(schema))})
        rs.close()
        c.close()
        return return_set



    def sql_create_schema(self):
        try:
            c = self.connection.cursor()
            c.execute( """DROP TABLE idea_fetch""")
            c.close()
        except Exception as err:
            print ( err )
        try:
            c = self.connection.cursor()
            c.execute( """CREATE TABLE idea_fetch
                        (   fetch_id text,
                            url text,
                            hash text,
                            title text,
                            description text,
                            copy text,
                            user text,
                            idea_date real,
                            fetch_date real,
                            update_since real)""")
            c.close()
        except Exception as err:
            print ( err )
        try:
            c = self.connection.cursor()
            c.execute( """DROP TABLE anno_fetch""")
            c.close()
        except Exception as err:
            print ( err )

        try:
            c = self.connection.cursor()
            c.execute( """CREATE TABLE anno_fetch
                        (   fetch_id text,
                            anno_seq integer,
                            anno_text text,
                            anno_user text,
                            anno_date real
                            )""")
            c.close()
        except Exception as err:
            print ( err )
        try:

            c = self.connection.cursor()
            c.execute( """DROP TABLE link_fetch""")
            c.close()
        except Exception as err:
            print ( err )
        try:

            c = self.connection.cursor()
            c.execute( """CREATE TABLE link_fetch
                        (   fetch_id text,
                            link_seq integer,
                            link_url text,
                            link_rickroll text,
                            link_text text,
                            link_anno text,
                            link_user text,
                            link_date real
                            )""")
            c.close()
        except Exception as err:
            print ( err )

        try:
            c = self.connection.cursor()
            c.execute( """DROP VIEW fresh_ideas""")
            c.close()
        except Exception as err:
            print ( err )

        try:
            c = self.connection.cursor()

            latest_view_sql="""
                            CREATE VIEW fresh_ideas as
                            select  i.url url,
                                    i.fetch_id fetch_id,
                                    i.hash hash,
                                    i.fetch_date fetch_date
                                from
                                idea_fetch i join
                                    (select url, max(fetch_date) fetch_date from idea_fetch group by url) as lif
                                on i.url = lif.url and i.fetch_date = lif.fetch_date
                                order by i.fetch_date
            """

            c.execute(latest_view_sql)
            c.close()
        except Exception as err:
            print ( err )

        try:
            c = self.connection.cursor()
            c.execute( """DROP VIEW latest_user_content""")
            c.close()
        except Exception as err:
            print ( err )

        try:
            c = self.connection.cursor()

            user_content_sql="""
                    CREATE VIEW latest_user_content
                    as

                    select f.url, i.fetch_id, i.idea_date date, user, "idea_title" ctype, -3 seq, title text
                                    from
                                    idea_fetch i
                                    join fresh_ideas f on i.fetch_id = f.fetch_id
                    union all
                        select f.url, i.fetch_id, i.idea_date date, user, "idea_description" ctype, -2 seq, description text
                                    from
                                    idea_fetch i
                                    join fresh_ideas f on i.fetch_id = f.fetch_id
                    union all
                        select f.url, i.fetch_id, i.idea_date date, user, "idea" ctype, -1 seq, copy text
                                    from
                                    idea_fetch i
                                    join fresh_ideas f on i.fetch_id = f.fetch_id

                    union all
                        select f.url, a.fetch_id, anno_date date, anno_user user, "anno" ctype, anno_seq seq, anno_text text
                                    from
                                    anno_fetch a
                                    join fresh_ideas f on a.fetch_id = f.fetch_id
                    union all
                        select f.url, l.fetch_id, link_date date, link_user user, "link" ctype, link_seq seq, link_text || " " || link_anno text
                                    from
                                    link_fetch l
                                    join fresh_ideas f on l.fetch_id = f.fetch_id
                    order by date, seq, url
            """

            c.execute(user_content_sql)
            c.close()

        except Exception as err:
            print ( err )

        self.connection.connit()



        return True

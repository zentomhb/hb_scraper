import ScrapeBakery as sb
import dateparser
import pandas as pd
import datetime
import re


def collect_ideas(first_time=True):
    now = datetime.datetime.now().timestamp()
    # This makes use of a search url, returning all the ideas posted in some time period (defaulted to a day)
    a_day = 86400
    print (first_time)
    if first_time == True:
        days_since_start = (datetime.datetime.now() - datetime.datetime(2020,10,17) ).days

        start_timestamp = now-(a_day * days_since_start)
        guess_m = 500
        t_minus = int(now - start_timestamp)
        urls = ["https://www.halfbakery.com/view/ftm=r{t_minus}:s=Qr:d=irq:dn={m}:ds=0:n=Today_27s_20Notions:i=A_20list_20of_20todays_20ideas_20and_20annotations:t=Today_27s_20Notions".format(m=guess_m,t_minus=t_minus),
                "https://www.halfbakery.com/view/ftm=r{t_minus}:s=Qr:d=irq:do=100:dn=100:ds=0:n=Today_27s_20Notions:i=A_20list_20of_20todays_20ideas_20and_20annotations:t=Today_27s_20Notions".format(t_minus=t_minus),
                "https://www.halfbakery.com/view/ftm=r{t_minus}:s=Qr:d=irq:do=200:dn=100:ds=0:n=Today_27s_20Notions:i=A_20list_20of_20todays_20ideas_20and_20annotations:t=Today_27s_20Notions".format(t_minus=t_minus),
                "https://www.halfbakery.com/view/ftm=r{t_minus}:s=Qr:d=irq:do=300:dn=100:ds=0:n=Today_27s_20Notions:i=A_20list_20of_20todays_20ideas_20and_20annotations:t=Today_27s_20Notions".format(t_minus=t_minus),
               "https://www.halfbakery.com/view/ftm=r{t_minus}:s=Qr:d=irq:do=400:dn=100:ds=0:n=Today_27s_20Notions:i=A_20list_20of_20todays_20ideas_20and_20annotations:t=Today_27s_20Notions".format(t_minus=t_minus)]

    else:
        start_timestamp = now-(a_day * 3)
        guess_m = 100
        t_minus = int(now - start_timestamp)
        urls = ["https://www.halfbakery.com/view/ftm=r{t_minus}:s=Qr:d=irq:dn={m}:ds=0:n=Today_27s_20Notions:i=A_20list_20of_20todays_20ideas_20and_20annotations:t=Today_27s_20Notions".format(m=guess_m,t_minus=t_minus)]

    print ("Search urls", urls)
    data_harvest = sb.HarvestLinks(urls, start_timestamp)
    print("Number of unique links to follow: {l}".format(l=len(data_harvest.fetch_links)))
    data_harvest.fetch_data()
    return data_harvest.contents

def save_ideas(data_store, ideas):
    for idea in ideas:
        data_store.save_idea(idea)

def multi_matcher(text, match_d):
    matches={}
    wbs=[]
    wb_regex=re.compile(r"(\b)")
    for m in wb_regex.finditer(text):
        if m is not None:
            wbs.append(m.span()[0])
    for k,v in match_d.items():
        matches[k]=[]
        for vv in v:
            m = vv.finditer(text)
            if m is not None:
                for mg in m:
                    sp=mg.span()
                    try:
                        start_pos = [w for w in wbs if w < sp[0]-10][-1]
                    except IndexError:
                        start_pos = 0
                    try:
                        end_pos = [w for w in wbs if w > sp[1]+10][0]
                    except IndexError:
                        end_pos = len(text)
                    matches[k].append ((sp, "//" + text[start_pos:end_pos] + "//"))
    for k in matches.keys():
        if matches[k]==[]:
            matches[k]=None
    matches = {k:v for k,v in matches.items() if v is not None}
    return matches


def perform_matches(data_store, match_config_d):
    now = datetime.datetime.now().timestamp()
    contribution_df = pd.DataFrame(data_store.query_to_recordset("select * from latest_user_content")).sort_values(by=["date","seq"])
    hmatch = contribution_df['text'].apply(lambda x : multi_matcher(x, match_config_d))
    for k in match_config_d.keys():
        matches=hmatch.apply(lambda x : k in x.keys())
        kmatches=hmatch[matches].apply(lambda x : x.get(k))
        not_exclusions = contribution_df["url"].apply(lambda x : x not in ["https://www.halfbakery.com/idea/F_fcrst_20annual_20HalfBakery_20_93Wo_20ist_20der_20F_fchrer_20_3f_94_20programming_20competition_2e", "https://www.halfbakery.com/idea/Days_20Since_20Hitler_20Was_20Mentioned_20Here"])
        findex=((matches) & (not_exclusions))
        f_df = contribution_df[findex]
        f_df['matches']=kmatches
        print()
        try:
            final_mention = f_df.loc[f_df.groupby("date").seq.idxmax()].iloc[-1]
            #penultimate_mention = f_df.loc[f_df.groupby("date").seq.idxmax()].iloc[-2]
            #last_period = (final_mention['date']-penultimate_mention['date'])/86400
            mention_period = int((now - final_mention['date'])/86400)
            t = data_store.query_to_recordset("select distinct title from idea_fetch where url=?",[final_mention['url']])
            #print(t[0]['title'])

            print("It has been {d} days since {t} was last mentioned.".format(d=int(mention_period),t=k))
            print("{c} found on {l} by [{u}] {t} on {d}".format(c=final_mention['ctype'], l=t[0]['title'], u=final_mention['user'], t=final_mention['matches'][0][1].replace("\n", "").replace("\r", ""), d=datetime.datetime.fromtimestamp(final_mention['date']).strftime("%d %b %Y")))
            #print ( final_mention )
        except IndexError as err:
            #print("{t}\t".format(t=k), err)
            print("No mention of {t} found in the cache.".format(t=k))


#download cx-section-titles-aligned.db
#wget https://people.wikimedia.org/~santhosh/cx-section-titles-aligned.db
import sqlite3
import pandas as pd
import requests


con = sqlite3.connect("cx-section-titles-aligned.db")
translations = pd.read_sql_query("""SELECT * from titles """, con)


# In[155]:


def getMapping(source_lang,target_lang,source_title):
    global translations
    df = translations[(translations.source_language ==source_lang) & (translations.source_title ==source_title) &
                     (translations.target_language ==target_lang)]
    if not df.target_title.empty:
        candidates = set(df.target_title)
    else:
        candidates = set()
    ## Assuming that translations are bijective A -> B, implies B -> A
    df = translations[(translations.source_language ==target_lang) & (translations.target_title ==source_title) &
                     (translations.target_language ==source_lang)]
    if not df.source_title.empty:
        candidates = candidates.union(set(df.source_title))
    return candidates




def getLangLinkgs(source_lang,target_lang,source_page):
    # Basic function get the corresponding article in the target language
    baseurl = 'https://%s.wikipedia.org/w/api.php?action=query&format=json&prop=langlinks&titles=%s&lllimit=500&lllang=%s' % (source_lang,source_page,target_lang)
    response = requests.get(baseurl).json()
    try:
        return list(response['query']['pages'].values())[0]['langlinks'][0]['*']
    except:
        return False





def getSections(lang,article,Maxtoclevel = 3):
    #Function to extract sections from a Given Article
    #Maxtoclevel indicates the section depth we want to consider 
    baseurl = 'https://%s.wikipedia.org/api/rest_v1/page/mobile-sections/%s' % (lang,article)
    response = requests.get(baseurl).json()
    try:
        return set([sec.get('line') for sec in response['lead']['sections'] if (sec.get('line',0) !=0) & (sec.get('toclevel',0) <=Maxtoclevel)]) 
    except:
        return []


# In[151]:


def findMissingSections(source_lang,target_lang,source_page,Maxtoclevel=3):
    target_page = getLangLinkgs(source_lang,target_lang,source_page)
    target_sections = getSections(target_lang,target_page,Maxtoclevel=3)
    source_sections = getSections(source_lang,source_page,Maxtoclevel=Maxtoclevel)
    translate = []
    for section in source_sections:   
        candidates = getMapping(source_lang,target_lang,section)
        if not candidates:
            candidates = set()
        if not candidates & target_sections:
            translate.append(section)
    return translate
    

from flask import jsonify
from flask import Flask
app = Flask(__name__)


@app.route('/<source_lang>/<target_lang>/<source_article>/')
@app.route('/<source_lang>/<target_lang>/<source_article>/<Maxtoclevel>')
def summary(source_lang,target_lang,source_article,Maxtoclevel=2):
    d = findMissingSections(source_lang,target_lang,source_article)
    return jsonify(d)

@app.route('/<path:dummy>')
def fallback(dummy):
    return '''
	   <h2> Wrong URL</h2>
	   Please use https://cxsectionrec.wmflabs.org/source_lang/target_lang/source_article/toclevel:optional <br> <br>
	   For example: <br>
		<li> <a href='https://cxsectionrec.wmflabs.org/en/es/Ukulele/1'>  https://cxsectionrec.wmflabs.org/en/es/Ukulele/1 <a> </li>
		<li>		<a href='https://cxsectionrec.wmflabs.org/en/es/Ukulele/'>  https://cxsectionrec.wmflabs.org/en/es/Ukulele/ <a> </li>

		'''

@app.route('/')
def index():
 return '''
	   <h2> Sections to Translate </h2>
	   Please use https://cxsectionrec.wmflabs.org/source_lang/target_lang/source_article/toclevel:optional <br> <br>
	   For example: <br>
		<li> <a href='https://cxsectionrec.wmflabs.org/en/es/Ukulele/1'>  https://cxsectionrec.wmflabs.org/en/es/Ukulele/1 <a> </li>
		<li>		<a href='https://cxsectionrec.wmflabs.org/en/es/Ukulele/'>  https://cxsectionrec.wmflabs.org/en/es/Ukulele/ <a> </li



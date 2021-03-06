import re, string, calendar
from wikipedia import page
from bs4 import BeautifulSoup
from nltk import word_tokenize, pos_tag, ne_chunk
from nltk.tree import Tree

def get_page_html(title):
	return page(title).html()

def get_first_infobox_text(title):
	html = get_page_html(title)
	return clean_text(get_first_infobox(html).text)

def get_first_infobox(html):
	soup = BeautifulSoup(html, 'html.parser')
	results = soup.find_all(class_ = 'infobox')
	
	if not results:
		raise LookupError('Page has no infobox')
	
	return results[0]

def clean_text(text):
	only_ascii = ''.join([char if char in string.printable else ' ' for char in text])
	no_dup_spaces = re.sub(' +', ' ', only_ascii)
	no_dup_newlines = re.sub('\n+', '\n', no_dup_spaces)
	return no_dup_newlines

def get_match(text, pattern, error_text = "Page doesn't appear to have the property you're expecting"):
	p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
	match = p.search(text)

	if not match:
		raise AttributeError(error_text)

	return match

def get_planet_radius(title):
	infobox_text = get_first_infobox_text(title)
	pattern = r'(?:Polar radius.*?)(?: ?[\d]+ )?(?P<radius>[\d,.]+)(?:.*?)km'
	error_text = "Page infobox has no polar radius information."
	match = get_match(infobox_text, pattern, error_text)

	return match.group('radius')

def get_birth_date(title):
	infobox_text = get_first_infobox_text(title)
	pattern = r'(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})'
	error_text = "Page infobox has no birth information. At least none in xxxx-xx-xx format"
	match = get_match(infobox_text, pattern, error_text)

	return match.group('birth')

def get_trial_ddate(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'Decided(\s+)(?P<ddate>[a-z]+\s[\d]{1,2},\s[\d]{4})'
    error_text = "Page infobox has no decision date information. At least none in Month-xx-xxxx format"
    match = get_match(infobox_text, pattern, error_text)

    return match.group('ddate')

def get_hex_triplet(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'(?P<color>#\w{6})'
    error_text = "Page infobox has no hex triplet information. At least none in the #xxxxxx format"
    match = get_match(infobox_text, pattern, error_text)
    
    return match.group('color')

def get_RGB(title):
    infobox_text = get_first_infobox_text(title)
    pattern = r'\(r, g, b\)\n(?P<RGB>\([\d]+, [\d]+, [\d]+\))'
    error_text = "Page infobox has no country information."
    match = get_match(infobox_text, pattern, error_text)

    return match.group('RGB')


def match(pattern, source):
    """Match takes a pattern and a source - both lists of strings.  It
    returns None if the source does not match the pattern.  Otherwise, if the
    source does match the pattern, it returns a list of the substitutions
    to get from the pattern to the source."""
    pind,sind = 0,0
    matches = []
    accumulator = ""
    accumulating = False
    while True:
        if len(pattern) == pind and len(source) == sind:
        # Both lists end simultaneously: clean up and return
            if accumulating:
                matches = matches + [accumulator.lstrip()]
            return matches

        elif len(pattern) == pind:
        # Pattern ends before source: continue accumulating, if
        # appropriate, or else signal that there is no match
            if accumulating:
                accumulator = accumulator + " " + source[sind]
                sind = sind + 1
            else:
                return None

        elif pattern[pind] == "%":
        # Pattern has not ended: begin accumulating
        # Since we disallow "% %", accumulating is False at this point.
            accumulating = True
            accumulator = ""
            pind = pind + 1

        elif len(source) == sind:
        # Source ends before pattern complete: signal that there
        # is no match
            return None

        elif pattern[pind] == "_":
        # Neither has ended: add a singleton
        # Since we disallow "% _", accumulating is False at this point.
            matches = matches + [source[sind]]
            pind = pind + 1
            sind = sind + 1

        elif pattern[pind] == source[sind]:
        # Neither has ended and the words match: stop accumulating and
        # continue
            if accumulating:
               accumulating = False
               matches = matches + [accumulator.lstrip()]
            pind = pind + 1
            sind = sind + 1

        else:
        # Neither has ended and the words do not match: continue
        # accumulating or signal that there is no match.
            if accumulating:
                accumulator = accumulator + " " + source[sind]
                sind = sind + 1
            else:
                return None

# Below are a set of actions.  Each takes a list argument and returns 
# a list of answers according to the action and the argument.
# It is important that each function returns a list of the answer(s)
# and not just the answer itself.
def birthDate(argList):
    """birthDate takes a list of arguments (returned from the match function).
    It takes the name of the person and returns that person's birth date"""
    person = ' '.join(argList)
    return [get_birth_date(person)]

def polarRadius(argList):
    """planetRadius takes a list of arguments (returned from the match function).
    It takes the name of the planet and returns that planet's polar radius"""
    planet = argList[0]
    return [get_planet_radius(planet)]

def ddate(argList):
    """ddate takes a list of arguments (returned from the match function).
    It takes the name of the trial case and returns the decision date of the trial."""
    trialcase = ' '.join(argList)
    return [get_trial_ddate(trialcase)]

def hextriplet(argList):
    """hextriplet takes a list of arguments (returned from the match function).
    It takes the name of the color and returns the hex triplet of the color."""
    color = argList[0]
    return [get_hex_triplet(color)]

def RGB(argList):
    color = argList[0]
    return [get_RGB(color)]

def byeAction(dummy):
    raise KeyboardInterrupt

#  The pattern-action list for the natural language query system.
#  It must be declared here, after all of the function definitions.
paList = [    
    ('when was % born'.split(),                     birthDate),
    ('what is the polar radius of %'.split(),       polarRadius),
    ('what is the decision date of case %'.split(), ddate),
    ('what is the hex triplet of %'.split(),        hextriplet),
    ('what is the rgb value of %'.split(),          RGB),
    (['bye'],                                       byeAction)
]

#  The search routine. It searches through a list of pattern-action pairs
#  named paList, lookng for matches (calling match on each pattern). If it
#  finds a match, it takes the corresponding action and accumulates the
#  answers in a result list, to be returned at the end.
def searchPAList(src):
    """takes a source as a list of strings, finds the matching pattern ands
    calls the appropriate action, passing it the results from match. If it 
    finds a match, but has no answers, then returns ["None"]. If it doesn't
    find a match, returns ["I don't understand."]"""
    numMatches = 0
    resultList = []
    for pat, act in paList:
        mat = match(pat, src)
        if mat != None:
            numMatches += 1
            resultList += act(mat)
    if not numMatches:
        return ["I don't understand."]
    elif not resultList:
        return ["None."]
    else:
        return resultList

#  The simple query loop. The try/except structure is to catch ctrl-C
#  or ctrl-D characters and exit gracefully.
def queryLoop():
    print "Welcome to the Wikipedia chatbot!"
    
    while True:
        try:
            query = raw_input("\nYour query?").replace('?', '').lower().split()
            answers = searchPAList(query)
            for ans in answers:
                print ans
        except (KeyboardInterrupt, EOFError):
            break

    print "\nSo long!\n"

queryLoop()

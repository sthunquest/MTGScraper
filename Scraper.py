import urllib.request
import re
import sqlite3




test = """html xmlns="http://www.w3.org/1999/xhtml">
<head><title>
	Ankh of Mishra (Limited Edition Alpha) - Gatherer - Magic: The Gathering
</title><link rel="sho"""
#Opens a url-String and returns a responcePage object. Handles redirect
def openPage(urlString):
    page = urllib.request.Request(urlString)
    responcePage = urllib.request.urlopen(page)
    return responcePage
# Decodes a ResponcePage into a 'UTF-8' String
def decodePage(responceObject):
    htmlCode = responceObject.read()
    decodedHtml = htmlCode.decode('UTF-8')
    strToSearch = ""
    for line in decodedHtml:
        strToSearch += line
    return strToSearch
# returns a string of '<start tag>...</end tag>'
def findTag(tagOpen, tagClose, strPage):
    tagFinder = re.compile(tagOpen+'[\D*|(.*)]*'+tagClose)
    return (re.search(tagFinder, strPage).group())
#returns the CardName from within title tags
def refineTitle(rawTitle):
    newTitle = ''
    tag = '<title>'
    startTagIndex = rawTitle.find(tag)
    endTitleIndex = rawTitle.find(""" (""")
    newTitle += (rawTitle[(startTagIndex+len(tag)):endTitleIndex]).strip()
    return newTitle

def refineTag(startTag,endTag, rawTag):
    newTag = ''
    startTagIndex = rawTag.find(startTag)
    endTitleIndex = rawTag.find(endTag)
    newTag += (rawTag[(startTagIndex+len(startTag)):endTitleIndex]).strip()
    return newTag
def tagSearch(startTag, endTag, rawTag):
    newTag = ''
    startIndex = rawTag.find(startTag)
    endIndex = rawTag[startIndex:].find(endTag)+startIndex
    newTag = rawTag[startIndex:endIndex]
    return newTag
def getCardName( decodedPage):
    nameExists = decodedPage.find("""Card Name:""")
    if nameExists == -1:
        return None
    return (refineTag('<title>',""" (""",decodedPage))
def extractType(typeBlockMess):
    newType=''
    divClosed = False
    startCapture = typeBlockMess.find('>')
    stopCapture = typeBlockMess[1:].find('<')
    newType = (typeBlockMess[startCapture+1:stopCapture+1].strip())
    return newType 
def extractMana(focusGroup):
    manaCost = []
    tag = r'alt="'
    endTag = r'"'
    if focusGroup.find(tag) != -1:
        startCapture = focusGroup.find(tag)+len(tag)
        stopCapture = focusGroup[startCapture:].find(endTag)
        add = focusGroup[startCapture:startCapture+stopCapture]
        manaCost.insert(len(manaCost), add)
        manaCost += extractMana(focusGroup[startCapture+stopCapture+len(endTag):])
    return manaCost

    
def extractText (focusGroup):
    newText = ''
    tag = r';">'
    startText = focusGroup.find(tag)
    newText = focusGroup[startText+len(tag):]
    return newText
            
def getCardType(decodedPage):
    typeBlock = refineTag("Types:</div>", "Card Text:", decodedPage)
    
    return(extractType(typeBlock))

def listCards(cardList):
    for card in cardList:
        print(card)

    return
def getCardsDB(start, end):
    cardDB = sqlite3.connect('card.db')
    cursor = cardDB.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cards(idNumber INTEGER PRIMARY KEY,
    cardNumber INTEGER,
    name TEXT,
    type TEXT,
    cost TEXT,
    text TEXT,
    flavor TEXT,
    pt TEXT,
    rarity TEXT,
    expansion TEXT,
    image TEXT)
    
    ''')
    for i in range(start,end):
        card = Card(i)
        if card.cardName != None:
            print(card.flavorText)
            cursor.execute('''INSERT INTO cards(cardNumber, name, type, cost, text, flavor, pt, rarity, expansion, image)VALUES(?,?,?,?,?,?,?,?,?,?)''',
                           (i,
                            card.cardName,
                            card.cardType,
                            str(card.manaCost),
                            card.cardText,
                            card.flavorText,
                            card.pT,
                            card.rarity,
                            str(card.expansion),
                            card.imgURL))    
        cardDB.commit()
    #cardDB.close()
    return cardDB
def printDB(cardDB):
    cursor = cardDB.cursor()
    cursor.execute('SELECT * FROM cards ORDER BY cardNumber')
    for i in cursor:
        print("\n")
        for j in i:
            print(j)
    return
def db():
    return getCardsDB(0,0)
def formatPrintDB(cardDB):
    cursor = cardDB.cursor()
    cursor.execute('SELECT * FROM cards ORDER BY cardNumber')
    for i in cursor:
        print("\n")
        print("********************************************\n")
        print("*"+i[2]+"       "+i[4]+"\n*\n*\n*\n")
        print("*"+i[3]+"      "+i[8]+"-"+i[9]+"\n")
        print("*---------------------------------------------*\n")
        print("*| "+i[5]+"\n*|\n")
        print("*| "+((i[6])if(i[6]!=None)else(""))+"\n")
        print("*|_____________________________"+i[7]+"_______*")
        print("************"+str(i[0])+","+str(i[1])+"**************")
    return
def getCardList(cardCount):
    listOfCards=[]                                        
    for i in range(1,cardCount):
        listOfCards.append(getCardName(decodePage(openPage('http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=%d'%i))))
    return listOfCards
def getExpansion(decodedPage):
    focusGroup = ''
    if decodedPage.find(r'Expansion:') == -1:
        return ''
    focusGroup = refineTag(r'Expansion:</div>',r'Rarity:',decodedPage)
    return extractMana(focusGroup)
def getAllSets(decodedPage):
    focusGroup = ''
    if decodedPage.find(r'All Sets:') == -1:
        return []
    focusGroup = refineTag(r'All Sets:</div>',r'Artist:',decodedPage)
    return extractMana(focusGroup)
def getManaCost(decodedPage):
    focusGroup = ''
    if decodedPage.find(r'Mana Cost:')== -1:
        return []
    focusGroup = refineTag(r'Mana Cost:</div>',r'Converted Mana Cost:', decodedPage)
    costTags=r'alt="'
    manaCost = ''
    manaCost = extractMana(focusGroup)
    return manaCost
def getCardText(decodedPage):
    textExists = decodedPage.find("""Card Text:""")
    if textExists == -1:
        return ''
    focusGroup = refineTag(r'Card Text:</div>',r'</div></div>', decodedPage)
    return extractText(focusGroup)

def getFlavorText(decodedPage):
    flavorExists = decodedPage.find("""Flavor Text:""")
    spacePat = r'<div class=\'cardtextbox\'>'
    div = r'</?div>'
    ital = r'</?i>'
    pad = """<div class="cardtextbox" style="padding-left:10px;">"""
    otherTags = r'<.*?>'
    if flavorExists != -1:
        #print("flavor found")
        blockFlavor = tagSearch("""Flavor Text:""", '<div class="label">', decodedPage)
        reSpacePat = re.compile(spacePat)
        reDiv = re.compile(div)
        reItal = re.compile(ital)
        rePad = re.compile(pad)
        reOTag = re.compile(otherTags)
        formFlavor = reSpacePat.sub('\n', blockFlavor)
        divFlavor = reDiv.sub(r'', formFlavor)
        italFlavor = reItal.sub(r'', divFlavor)
        padFlavor = rePad.sub('\n', italFlavor)
        flavor = reOTag.sub(r'', padFlavor)
        
        
        return flavor[12:].strip()
    else:
        return None

def getRarity(decodedPage):
    startTag = r'Rarity:</div>'
    endTag = r'All Sets:</div>'
    rarity = decodedPage
    workingRarity = rarity[rarity.find(startTag)+len(startTag):rarity.find(endTag)]
    sStartTag = '\'>'
    sStopTag = r'</span>'
    finalRarity = workingRarity[workingRarity.find(sStartTag)+len(sStartTag):workingRarity.find(sStopTag)]
    return finalRarity

def getPT(decodedPage):
    startTag = r'P/T:</b></div>'
    endTag = r'Expansion:</div>'
    rawPT = refineTag(startTag, endTag, decodedPage)
    startTag = """class="value">"""
    endTag = r'</div>'
    rePT = refineTag(startTag, endTag, rawPT)
    return rePT

def replaceAlt(rawText):
    pad = """<div class="cardtextbox" style="padding-left:10px;">"""
    rEPad = re.compile(pad)
    altTag = r'<img.*?alt=\"(\w+)\".*?/>'
    rEAlt = re.compile(altTag)
    newText = rEPad.sub('\n', rawText)
    altText = rEAlt.sub(r'\1'+' ', newText)
    div = r'</?div>'
    ital = r'</?i>'
    rEDiv = re.compile(div)
    rEItal = re.compile(ital)
    almostFinalText = rEDiv.sub(r'', altText)
    finalText = rEItal.sub(r'', almostFinalText)
    return finalText
def setStrip(expansion):
    return expansion[0][:(expansion[0].find('(')-1)]
def setListStrip(page):
    focusGroup = refineTag(r' Card Set:',r'Card Type:</p>', page)
    return focusGroup
def setList(url):
    decodedPage = decodePage(openPage(url))
    return setFormLoop(setListStrip(decodedPage))
    
def setFormLoop(page):
    inForm = False
    setString = ''
    setList =[]
    for i in page:
        if i == '<':
            inForm = True
        elif i == '>':
            inForm = False
        elif i == '=':
            setList = setList + [setString.strip()]
            setString = ''
                
        elif (inForm) == False:
            setString = setString + i

    secondList = []
    for j in setList:
        secondList =secondList + [replaceAlt(j)]
          
    return secondList[5:]
   
            
class Card:
    def __init__(self,cardNumber):
        self.cardNumber = cardNumber
        self.url = 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=%d'%self.cardNumber 
        self.imgURL = 'http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid='+str(self.cardNumber)+'&type=card'
        self.decodedPage = decodePage(openPage(self.url))
        self.cardName = getCardName(self.decodedPage)
        self.cardType = getCardType(self.decodedPage)
        self.manaCost = getManaCost(self.decodedPage)
        self.flavorText = getFlavorText(self.decodedPage)
        self.cardText = replaceAlt(getCardText(self.decodedPage))
        self.rarity = getRarity(self.decodedPage)
        self.expansion = setStrip(getExpansion(self.decodedPage))
        self.allSets = getAllSets(self.decodedPage)
        try:
            self.pT = getPT(self.decodedPage)
        except:
            self.pT = ''

    def pv(self):
        print(self.cardName)
        print(self.manaCost)
        print(self.cardType)
        print(self.expansion)
        print(self.rarity)
        print(self.cardText)
        print(self.flavorText)
        print(self.pT)
        print(self.allSets)
        print(self.imgURL)
        
        
        
        
homeurl = 'http://gatherer.wizards.com/Pages/Default.aspx'        

pageurl = 'http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=1'
imgurl = 'http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=661&type=card'
cardTest = Card(6082)
cardTest.pv()
#cardName =refineTag('<title>',""" (""",decodePage(openPage(pageurl)))
#print(cardName)
#x=decodePage(openPage(pageurl))
#y=refineTag("Types:</div>", "Card Text:", x)
#cardType = extractType(y)
#print (cardType)



"""nameFinder = re.compile('<title>\D*(.*)</title>')
name = re.search(nameFinder, strToSearch)"""





from autocorrect import Speller
from nltk.chat.util import Chat, reflections
from nltk.tokenize import wordpunct_tokenize
from stopwords import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from language_pairs import pairs
from nltk.corpus import wordnet
import python_weather
import asyncio
import geonamescache
from datetime import datetime
import wikipediaapi


def generate_token(msg):
    """Tokenize response and remove all stop words to simplify the statement"""
    text_tokens = wordpunct_tokenize(msg)
    tokens_without_sw = [word for word in text_tokens if not word in stopwords]

    return tokens_without_sw


async def weather_api(message):

    location_i = message.index("weather") + 1
    location = message[location_i]
    print(message)
    gc = geonamescache.GeonamesCache()
    city = gc.search_cities(location, case_sensitive=False)
    if not city:
        return " ".join(message)

    client = python_weather.Client(format=python_weather.METRIC)

    weather = await client.find(location)

    await client.close()

    return weather.forecasts

def wiki_api(message):

    wiki_search = " ".join(message)
    wiki_wiki = wikipediaapi.Wikipedia('en')

    wiki_page = wiki_wiki.page(wiki_search)

    if wiki_page.exists() == False:
        return None

    wiki_title = wiki_page.title
    wiki_summary = wiki_page.summary[0:250]
    wiki_url = wiki_page.fullurl

    return f'I found the page {wiki_title} on wikipedia\n\nHere is a Summary:\n{wiki_summary}\n\nYou can read the article here: {wiki_url}'



def Detect_Synonym(msg):
    text_tokens = msg.split()                           ## tokenizes based on spaces, does not make `'` a separate token
    pair_tokens = []
    for elem in pairs:
        pair_tokens.append(elem[0].split())

    new_input = []
    for elem in pair_tokens:
        if len(elem) is not len(text_tokens):           ## checks token length of user input, and makes sure it matches expected pair (EP)input
            continue
        
        new_input = []
        for i in range(len(text_tokens)):               ## loops through each work/token in EP input 
            if elem[i] == text_tokens[i]:                         
                new_input.append(elem[i])               ## if the the two words match, add to  
            else:
                for syn in wordnet.synsets(elem[i]):    ## if they do not match, loop thru EP input word synonyms, 
                    found = False

                    for l in syn.lemmas():
                        if l.name() == text_tokens[i]:  ## if the proposed synonym matches the user input
                            new_input.append(elem[i])   ## add the synonym to te new_input, then break out of two loops
                            found = True
                            break
                    if found:
                        break

    return " ".join(new_input)                          ## Makes the new_input list a string unput


class Botler:
    """This is the bolter class it is in charge of maintaining the conversation"""

    def __init__(self):
        """Creates chat object from NLTK"""
        self.chat = Chat(pairs, reflections)
        self.name = "Botler"
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.speller = Speller()

    def generate_response(self, msg):
        # Correct any spelling mistakes
        clean_input = self.speller(msg)

        # Generate a response from the chatbot
        response = self.chat.respond(clean_input)

        # If response is still none, tokenize words
        if not response:
            tokens_without_sw = generate_token(clean_input)

        # Check if the tokens have the word weather
        if "weather" in tokens_without_sw:
            loop = asyncio.get_event_loop()
            forcast = loop.run_until_complete(weather_api(tokens_without_sw))
            response = "Here is the forcast for the next week:\n\n"
            for f in forcast:
                response = response + f'On the {str(f.date.strftime("%b %d, %Y"))}\nit will be {f.temperature}°C and {f.sky_text}\n\n'
        elif any(word in 'what why where when who how' for word in msg):
            response = wiki_api(tokens_without_sw)
        else:
            response = self.chat.respond(" ".join(tokens_without_sw))
        
        # If not response:
        if not response:
            response = self.chat.respond(Detect_Synonym(clean_input))

        # Getting sia_value to hold the dictionary from polarity_scores
        sia_value = self.sentiment_analyzer.polarity_scores(clean_input) 

        # sia_value['compound'] holds overall sentiment. 

        if response:
            return response
        elif sia_value['compound'] <= -0.5:
            return("I'm sorry you feel that way, but I am\nunable to fix this for you.\nPlease ask something different.")
        elif sia_value['compound'] >= 0.5:
            return("I'm happy to hear that sir,\nalthough I don't quite know what to do with that\ninformation.\nWould you mind asking something else?")
        else:
            return("I didn't quite hear that sir,\nwould you mind repeating that?")
        

import httplib2 # Pip install httplib2 for this
import json
import re
import hashlib

# Some local values needed for the call
CALAIS_API_KEY = '' # Aquire this by registering at the Calais site
CALAIS_API_URL = 'http://api.opencalais.com/tag/rs/enrich'
CALAIS_ALLOWED_SIZE = 90000 # Max characters

def printable_only(text):
    # REturns only printable characters
    return re.sub(r'\W+', '', text)

def get_text():
    # Simple method to grab some test text.
    file = open('varner.txt')
    return printable_only(file.read(CALAIS_ALLOWED_SIZE))

class CalaisSocialTag:
    def __init__(self, ctag):
        """Class to handle Open Calais Social Tag Suggestions"""
        self.ctag = ctag
        self.group = ctag.get("_typeGroup")
        self.id = ctag.get("id")
        self.importance = ctag.get("importance")
        self.name = ctag.get("name")
        self.socialtag = ctag.get("socialTag")

    def __lt__(self, other):
        """Custom Sort method
        """
        return self.name < other.name

    def __unicode__(self):
        return u"%s - %s" % (self.importance, self.name)

    def __str__(self):
        return self.__unicode__().encode('ascii', 'ignore')

class CalaisEntity:
    def __init__(self, ctag):
        """Class to handle Open Calis entity suggestions."""
        self.ctag = ctag
        self.type = ctag.get("_type")
        self.group = ctag.get("_typeGroup")
        self.reference = ctag.get("_typeReference")
        self.name = ctag.get("name")
        self.relevance = ctag.get("relevance")
        self.instances = ctag.get("instances")
        self.resolutions = ctag.get("resolutions")
        self.nationality = ctag.get("nationality")

    def __lt__(self, other):
        """
        Basic Sort methodology
        """
        return self.name < other.name

    def __unicode__(self):
        return u"%s (%s) [%s] %d instances" % (self.name, self.type, self.relevance, len(self.instances))

    def __str__(self):
        return self.__unicode__().encode('ascii', 'ignore')

class CalaisTopic:
    def __init__(self, ctag):
        """Class to hangle Open Calais topic suggestions."""
        self.ctag = ctag
        self.group = ctag.get("_typeGroup")
        self.name = ctag.get("categoryName")
        self.category = ctag.get("category")
        self.score = ctag.get("score", 0)

    def __lt__(self, other):
        """Custom sort method.
        """
        return self.name < other.name

    def __unicode__(self):
        return u"%s - %s" % (self.score, self.name)

    def __str__(self):
        return self.__unicode__().encode('ascii', 'ignore')

class CalaisCall:
    def __init__(self, type='text/html', socialtags=True):
        """
        A class that handles connecting to the Open Calais API with content and returning the
        results.  You can see an sample of the output from Open Calais at
        http://www.opencalais.com/documentation/calais-web-service-api/interpreting-api-response/opencalais-json-output-format

        :param content: The content to be analyzed by the API.
        :param type: Content type being sent, standard html header content-type values
        :param socialtags: Enable socialTags mediaType in the Open Calais Return

        """
        self.headers = self._set_headers(type, socialtags)
        self.entities = {}
        self.topics = {}
        self.tags = {}

    def _set_headers(self, ctype, socialtags):
        headers = {
            'x-calais-licenseID': CALAIS_API_KEY,
            'content-type':  ctype,
            'accept': 'application/json',
        }
        if socialtags:
            headers["enableMetadataType"] = 'SocialTags'
        return headers

    def add_tag(self, id, tag):
        # Adds a tag if it does not already exist
        if id not in self.tags:
            self.tags[id] = CalaisSocialTag(tag)

    def add_topic(self, id, topic):
        # adds a topic if it does not already exist and if it does.
        if id not in self.topics:
            self.topics[id] = CalaisTopic(topic)

    def add_entity(self, id, entity):
        # adds an entity if it does not already exist or appends the instances if it does.
        if id in self.entities:
            self.entities[id].instances.append(entity.get("instances"))
        else:
            self.entities[id] = CalaisEntity(entity)

    def parse_text(self, text):
        """Query the Open Calais API if we have any content"""
        if not text:
            return None

        # Make the API call and return the results
        http = httplib2.Http()
        reponse, results = http.request(CALAIS_API_URL, 'POST', headers=self.headers, body=text)

        try:
            data = json.loads(results.decode('utf-8', 'ignore'))
            del data["doc"] # Throw this away to parse more cleanly

            for id, item in data.items():
                if item["_typeGroup"] == 'socialTag':
                    self.add_tag(item.get("name", "blank"), item) # Names are all that really matters here.
                if item["_typeGroup"] == 'entities':
                    raw_key = hashlib.sha1(item.get("_type", "blank"))
                    raw_key.update(item.get("name", "blank"))
                    key = raw_key.hexdigest()
                    self.add_entity(key, item)
                if item["_typeGroup"] == 'topics':
                    raw_key = hashlib.sha1(item.get("categoryName", "blank"))
                    raw_key.update(item.get("category", "blank"))
                    key = raw_key.hexdigest()
                    self.add_topic(key, item)
        except ValueError:
            pass

class CalaisWriter:
    # Down and dirty parse a file by iteration over it's lines and running an Open Calais analysys on it.

    def __init__(self, filename, line_batch=1125):
        self._line_cursor = 0 # keep a cursor for where we are in reading a line.
        self._line_batch = line_batch # The number of lines to process per batch.
        self.filename = filename
        file = open(filename) # The filename to parse.
        self.text_lines = file.readlines()
        self.calais = CalaisCall(type="text/txt")

    def _read_text(self):
        """Opens the file for reading.
        """
        next = self._line_cursor + self._line_batch
        text = "\n".join(self.text_lines[self._line_cursor:next])
        self._line_cursor = next
        return text

    def parse(self):
        """Parses the text from the designated file.
        """
        while self._line_cursor < len(self.text_lines):
            self.calais.parse_text(self._read_text())

    def write(self):
        """
        Write a crude text file of results.
        """
        outfilename = "calais_%s" % self.filename # terrible but works for now
        outfile = open(outfilename, 'w')
        outfile.write(u'TOPICS\n')
        topics = [x for x in self.calais.topics.values()]
        for topic in sorted(topics):
            outfile.write(topic.__unicode__().encode('utf-8', "ignore"))
            outfile.write(u'\n')
        outfile.write(u'TAGS\n')
        tags = [x for x in self.calais.tags.values()]
        for tag in sorted(tags):
            outfile.write(tag.__unicode__().encode('utf-8', "ignore"))
            outfile.write(u'\n')
        outfile.write(u'ENTITIES\n')
        entities = [x for x in self.calais.entities.values()]
        for entity in sorted(entities):
            outfile.write(entity.__unicode__().encode('utf-8', "ignore"))
            outfile.write(u'\n')
        outfile.close()

if __name__ == "__main__":
    parse_filenames = [] # Create a list of filenames you want to parse with Open Calais.
    for filename in parse_filenames:
        cw = CalaisWriter(filename)
        cw.parse()
        cw.write()
    
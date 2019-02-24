import requests
from bs4 import BeautifulSoup
import os
import sys

url = "http://bslsignbank.ucl.ac.uk/dictionary/search/"

class BSLHandler:
    def __init__(self):
        self.base = 'http://bslsignbank.ucl.ac.uk'
        self.cache = 'cache'
        self.output = 'output'
        self.lists = 'lists'
    def _query(self, q):
        r = requests.get(
            '{}/dictionary/search/'.format(self.base),
            params={'query': q}
        )
        soup = BeautifulSoup(r.text)
        search_results = soup.find('div', {'id': 'searchresults'})
        res = {}
        try:
            for i in search_results.findAll('a'):
                res[i.text] = i['href']
        except:
            # If we hit the exact page
            location = r.history[0].headers['Location']
            res[q] = location.split(self.base)[1]

        return res
    def _extract_video_iframe(self, url):
        # get the iframe
        r = requests.get(
            '{}{}'.format(self.base, url)
        )
        soup = BeautifulSoup(r.text)
        iframe = soup.find('iframe', {'id': 'videoiframe'})
        return iframe['src']
    def _video_file_from_iframe(self, iframe):
        r = requests.get(
            '{}{}'.format(self.base, iframe)
        )
        soup = BeautifulSoup(r.text)
        video = soup.find('source')
        return video['src']

    def query(self, sentence):
        files = []
        paths = []
        sentence_clean = ''.join(
            e for e in sentence.lower() if e.isalnum() or e.isspace()
        ).split(' ')
        for word in sentence_clean:
            query = self._query(word)
            # is it an exact match? Or did we find the word in the query.
            # check if word is in result, else drop word.
            if word in query:
                iframe = self._extract_video_iframe(query[word])
                files.append(self._video_file_from_iframe(iframe))
        # Now download the videos
        for file in files:
            filename = file.split('/')[-1]
            path = "{}/{}".format(self.cache, filename)
            paths.append(path)
            # Quick check...
            if filename in os.listdir(self.cache):
                continue

            # should cache these...
            r = requests.get('{}{}'.format(self.base, file))
            with open(path, 'wb') as f:
                f.write(r.content)
        # Now merge them.
        ## Generate the list file
        listid = os.urandom(8).encode('hex')
        listpath = '{}/{}'.format(self.lists, listid)
        with open(listpath, 'w') as f:
            f.write('\n'.join(map(lambda x: 'file \'../{}\''.format(x), paths)))
        ## Trigger ffmpeg
        outputpath = '{}/{}.mp4'.format(self.output, listid)
        os.system('ffmpeg -f concat -safe 0 -i {} -c copy {}'.format(listpath, outputpath))

        return outputpath

if __name__ == '__main__':
    a = BSLHandler()
    if len(sys.argv) != 2:
        print('ARGS YO')
        exit(-1)
    print(a.query(sys.argv[1]))

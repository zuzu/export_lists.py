import twitter  #  python-twitter
import csv
import cStringIO
import codecs 
from requests_oauthlib import OAuth1Session

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def _encode_utf8(self, val):
        if isinstance(val, (unicode, str)):
            return val.encode('utf-8')

        return val

    def writerow(self, row):
        self.writer.writerow([self._encode_utf8(s) for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def get_access_token(consumer_key, consumer_secret):

    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret)

    print 'Requesting temp token from Twitter'

    try:
        resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError, e:
        print 'Invalid respond from Twitter requesting temp token: %s' % e
        return
    url = oauth_client.authorization_url(AUTHORIZATION_URL)

    print ''
    print 'I will try to start a browser to visit the following Twitter page'
    print 'if a browser will not start, copy the URL to your browser'
    print 'and retrieve the pincode to be used'
    print 'in the next step to obtaining an Authentication Token:'
    print ''
    print url
    print ''

    pincode = raw_input('Pincode? ')

    print ''
    print 'Generating and signing request for an access token'
    print ''

    oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret,
            resource_owner_key=resp.get('oauth_token'),
            resource_owner_secret=resp.get('oauth_token_secret'),
            verifier=pincode
            )
    try:
        resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
    except ValueError, e:
        print 'Invalid respond from Twitter requesting access token: %s' % e
        return

    print 'Your Twitter Access Token key: %s' % resp.get('oauth_token')
    print '          Access Token secret: %s' % resp.get('oauth_token_secret')
    print ''

    return resp.get('screen_name'), resp.get('oauth_token'), resp.get('oauth_token_secret')


if __name__ == "__main__":
    consumer_key = raw_input('Enter your consumer key: ')
    consumer_secret = raw_input("Enter your consumer secret: ")
    screen_name, oauth_token, oauth_token_secret = get_access_token(consumer_key, consumer_secret)

    api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret,
                      access_token_key=oauth_token, access_token_secret=oauth_token_secret)
    
    for l in api.GetListsList(screen_name):
        print l.id, l.slug
        filename = "%s.csv" % l.full_name.replace('@', '').replace('/', '_')
        f = open(filename, 'w')
        writer = UnicodeWriter(f, quotechar='"')

        writer.writerow(('name', 'url', 'description', 'followers_count', 'friends_count', 'listed_count', 'statuses_count', 'homepage'))

        for m in api.GetListMembers(l.id, l.slug):
            writer.writerow((m.name, 'http://twitter.com/' + m.screen_name, m.description, m.followers_count, m.friends_count, m.listed_count, m.statuses_count, m.url))

        f.close()
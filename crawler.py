#!/usr/bin/env python
import certifi
import google as google
import requests
import yaml
import firebase_admin
import hashlib
import threading

from googlesearch import search
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
from urllib.parse import urlsplit

###############
# GLOBAL VARS #
###############
verbose_logging = False


# Simple way to create a structured way of printing log statements.
def log_print(msg, status='notice'):
    prefix = ''
    suffix = ''
    if status == 'error':
        print(prefix + '[ERROR]: ' + msg + suffix)
    elif status == 'notice':
        print(prefix + '[NOTICE]: ' + msg + suffix)
    elif status == 'critical':
        print(prefix + '[CRITICAL]: ' + msg + suffix)
    elif status == 'success' or status == 'ok':
        print(prefix + '[OK]: ' + msg + suffix)
    elif status == 'none':
        print(msg)
    else:
        print(prefix + '[NOTICE]: ' + msg + suffix)


######################
# CONFIG SEARCH INIT #
######################
print('Started at: ' + str(datetime.now()))

log_print('Initialising configuration file.')
config = ''
with open("crawler_config.yml", 'r') as config_stream:
    try:
        config = yaml.load(config_stream)
        # Log that the config was loaded successfully.
        log_print('Configuration loaded', 'success')
    except yaml.YAMLError as exc:
        log_print('Failed to initialise the configuration.', 'critical')
        print(exc)

#################
# FIREBASE INIT #
#################
log_print('Initialising Firebase configuration')

service_account_json_path = config['firebase']['service_account_json_path']
db_collection = config['firebase']['collection_name']
cred = credentials.Certificate(service_account_json_path)
default_app = firebase_admin.initialize_app(cred)
db = firestore.client()


#####################
# GENERAL FUNCTIONS #
#####################
def request_url(url):
    try:
        r = requests.get(url, verify=certifi.where(), allow_redirects=True, timeout=10)
        if verbose_logging:
            print(r.url)
            print(r.status_code)
            print(r.history)
        return [1, r.url, r.status_code, r.history]
    except requests.exceptions.SSLError as error:
        if verbose_logging:
            print(error)
        return [2, None, None, None]

    # TODO: This one isn't working correctly.
    # Test with https://www.reisroutes.be and http://www.reisroutes.be.
    # www.ancestry.com
    except requests.exceptions.RequestException as error:
        if verbose_logging:
            print(error)
        return [3, None, None, None]

    except requests.exceptions.ConnectTimeout as error:
        if verbose_logging:
            print(error)
        return [3, None, None, None]


# Where the magic happens.
def verify_url(url):
    # Strip off the http(s) part of the url if present.
    if 'https://' in url:
        url = url.replace('https://', '')
    elif 'http://' in url:
        url = url.replace('http://', '')

    # Strip of any trailing or leading slashes
    url = url.strip('/')

    log_print('Verifying URL: ' + url, 'ok')
    http_result = request_url('http://' + url)
    https_result = request_url('https://' + url)

    # Actual logic to determine if the url is safe or not.
    safe_to_visit = False
    # If we got an RequestException on both levels, we have a dead url most certainly
    if https_result[0] == 3 and http_result[0] == 3:
        safe_to_visit = None

    # If the https request failed, but http works, it's considered unsafe.
    if http_result[0] != 3 and https_result[0] == 3:
        safe_to_visit = False

    # If we have a dead URL we don't need to check the redirects and certificate errors.
    if safe_to_visit is not None:
        # We only have a safe website when we have NO certificate errors
        # and if HTTP is correctly redirected to HTTPS.
        if https_result[0] != 2 and http_result[0] != 2 and 'https://' in http_result[1] and 'https://' in https_result[1]:
            safe_to_visit = True

    if safe_to_visit:
        safety = True
        log_print('SAFE to visit', 'ok')
    elif safe_to_visit is None:
        safety = None
        log_print('DEAD URL', 'ok')
    else:
        safety = False
        log_print('UNSAFE to visit', 'ok')

    return safety


# Function to store data in Firebase.
def store_data(url, data):
    # Hash the url to use it as ID and safe the data object.
    db.collection(db_collection).document(hashlib.md5(url.encode()).hexdigest()).set(data)

# Function to do as a thread.
def verify_and_store_url(urls, search_string):
    for url in urls:
        doc_ref = db.collection(db_collection).document(hashlib.md5(url.encode()).hexdigest())
        try:
            doc = doc_ref.get()
            # If we're past this line, this means we found data and thus could skip it.
            continue
        except google.cloud.exceptions.NotFound:
            pass

        # Check if the URL is safe.
        safety = verify_url(url)

        # store the data in Firebase.
        data = {
            u'method': u'search',
            u'search_key': str(search_string),
            u'URL': str(url),
            u'safety': str(safety)
        }
        store_data(url, data)


######################
# GOOGLE SEARCH INIT #
######################
if config['google_search']['enabled']:
    log_print('Google Search enabled.')
    google_search_config = config['google_search']
    # Set some other variables.
    top_level_domain = google_search_config['top_level_domain']
    language = google_search_config['language']
    number_of_results = google_search_config['number_of_results']
    timeout = google_search_config['timeout']

    log_print('Initialising the Google Keywords configuration.')
    google_keywords_config = ''
    with open("google_keywords.yml", 'r') as keywords_stream:
        try:
            google_keywords_config = yaml.load(keywords_stream)
            log_print('Google Keywords configuration loaded', 'success')
        except yaml.YAMLError as exc:
            log_print('Failed to initialise the Google Keywords configuration.', 'critical')
            print(exc)

    # Load extra params from the config.
    force_include_links = google_keywords_config['force_include_links']
    exclude_urls = google_keywords_config['exclude_urls']
    search_strings = google_keywords_config['search_strings']

    ########################
    # FORCE INCLUDED LINKS #
    ########################
    if force_include_links is not None and len(force_include_links) > 0:
        log_print('Processing all force include links.')
        log_print('---------------------------------------------', 'none')
        for force_include_link in force_include_links:
            safety = verify_url(force_include_link)
            # store the data in Firebase.
            data = {
                u'method': u'force',
                u'URL': str(force_include_link),
                u'safety': str(safety)
            }
            store_data(force_include_link, data)
    else:
        log_print('No links force included.')

    ##################
    # SEARCH STRINGS #
    ##################
    if search_strings is not None and len(search_strings) > 0:
        log_print('Start searching for all keywords on Google')
        log_print('---------------------------------------------', 'none')

        threads = []
        for search_string in search_strings:
            log_print('Starting to search for: ' + search_string)

            counter = 0
            matched_urls = []
            # We keep searching until we reached the max results.
            for search_result in search(search_string, tld=top_level_domain, lang=language, pause=timeout):
                # Get the base domain of the URL.
                base_domain = "{0.scheme}://{0.netloc}/".format(urlsplit(search_result))

                # We need to skip all the exclude URL's.
                if any([excl in base_domain for excl in exclude_urls]):
                    continue

                # Check if the base URL isn't already in the matched_urls list.
                if base_domain in matched_urls:
                    continue

                # Increase the counter.
                counter += 1
                # Store the URLS in the matched urls array (so we're not doing two actions at the same time).
                matched_urls.append(base_domain)

                # Break the for loop if we reached the maximum results.
                if counter == number_of_results:
                    break

            # Create a thread to process all the URLS.
            thread = threading.Thread(target=verify_and_store_url, args=(matched_urls, search_string))
            thread.daemon = True
            threads.append(thread)
            thread.start()

        # Join all the threads so we can continue until they are finished.
        for thread in threads:
            thread.join()

    else:
        log_print('No search strings provided.')

print('Finished at: ' + str(datetime.now()))

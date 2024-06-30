def get_sources(self, video):
    hosters = []
    query = self._build_query(video)
    if video.video_type == VIDEO_TYPES.EPISODE:
        search_url = scraper_utils.urljoin(self.base_url, SEARCH_URL_TV % urllib.parse.quote_plus(query))
    elif video.video_type == VIDEO_TYPES.MOVIE:
        search_url = scraper_utils.urljoin(self.base_url, SEARCH_URL_MOVIE % urllib.parse.quote_plus(query))
    logging.debug("Search URL: %s", search_url)
    html = self._http_get(search_url, require_debrid=True)
    logging.debug("Retrieved HTML: %s", html)
    soup = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer('tbody'))
    logging.debug("Parsed HTML: %s", soup)

    items = []
    for entry in soup.select("tr"):
        columns = entry.find_all('td')
        name = columns[0].find_all('a')[1].text.strip()
        torrent_page = columns[0].find_all('a')[1].get('href')
        torrent_page_url = urllib.parse.urljoin(self.base_url, torrent_page)
        items.append((name, torrent_page_url))

    threads = []
    for item in items:
        thread = threading.Thread(target=self._fetch_source, args=(item, hosters))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return self._filter_sources(hosters, video)

def _fetch_source(self, item, hosters):
    try:
        name, torrent_page_url = item
        logging.debug("Fetching source for: %s", name)
        torrent_page_html = self._http_get(torrent_page_url)
        logging.debug("Retrieved torrent page html: %s", torrent_page_html)
        magnet = re.search(r'href\s*=\s*["\'](magnet:.+?)["\']', torrent_page_html, re.I).group(1)
        hosters.append({
            'url': magnet,
            'title': name,
            'class': self,
            'multi-part': False,
            'host': 'magnet',
            'quality': get_release_quality(name),
            'direct': False,
            'debridonly': True
        })
        logging.debug("Retrieved sources: %s", hosters[-1])
    except AttributeError as e:
        logging.error("Failed to append source: %s", str(e))
    except Exception as e:
        logging.error("Unexpected error: %s", str(e))

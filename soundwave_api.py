import mutagen
import sys
from bs4 import BeautifulSoup
import re

def eprint(*values, **kwargs):
    print(*values, file=sys.stderr, **kwargs)

SCRAPE_URLS = [
    'https://soundcloud.com/mt-marcy/cold-nights'
]

def find_script_urls(html_text):
    dom = BeautifulSoup(html_text, 'html.parser')
    scripts = dom.findAll('script', attrs={'src': True})
    scripts_list = []
    for script in scripts:
        src = script['src']
        if 'cookielaw.org' not in src:  # filter out cookielaw.org
            scripts_list.append(src)
    return scripts_list


def find_client_id(script_text):
    client_id = re.findall(r'client_id=([a-zA-Z0-9]+)', script_text)
    if len(client_id) > 0:
        return client_id[0]
    else:
        return False

def get_large_artwork_url(artwork_url):
    return artwork_url.replace('large', 't300x300') if artwork_url else None

from urllib.request import urlopen
import json
import random
import io
import mutagen
from concurrent import futures
from ssl import SSLContext
ssl_verify=True

def get_ssl_setting():
    if ssl_verify:
        return None
    else:
        return SSLContext()

def get_url(url):
    return urlopen(url,context=get_ssl_setting()).read()

def get_page(url):
    return get_url(url).decode('utf-8')

def get_obj_from(url):
    try:
        return json.loads(get_page(url))
    except Exception as e:
        util.eprint(type(e), str(e))
        return False


class UnsupportedFormatError(Exception): pass

class SoundcloudAPI:
    __slots__ = [
        'client_id',
    ]
    RESOLVE_URL = "https://api-v2.soundcloud.com/resolve?url={url}&client_id={client_id}"
    SEARCH_URL  = "https://api-v2.soundcloud.com/search?q={query}&client_id={client_id}&limit={limit}&offset={offset}"
    STREAM_URL  = "https://api.soundcloud.com/i1/tracks/{track_id}/streams?client_id={client_id}"
    TRACKS_URL  = "https://api-v2.soundcloud.com/tracks?ids={track_ids}&client_id={client_id}"
    PROGRESSIVE_URL = "https://api-v2.soundcloud.com/media/soundcloud:tracks:723290971/53dc4e74-0414-4ab8-8741-a07ac56c787f/stream/progressive?client_id={client_id}"

    TRACK_API_MAX_REQUEST_SIZE = 50

    def __init__(self, client_id=None):
        if client_id:
            self.client_id = client_id
        else:
            self.client_id = None


    def get_credentials(self):
        url = random.choice(SCRAPE_URLS)
        page_text = get_page(url)
        script_urls = find_script_urls(page_text)
        for script in script_urls:
            if not self.client_id:
                if type(script) is str and not "":
                    js_text = f'{get_page(script)}'
                    self.client_id = find_client_id(js_text)

    def resolve(self, url):
        if not self.client_id:
            self.get_credentials()
        url = SoundcloudAPI.RESOLVE_URL.format(
            url=url,
            client_id=self.client_id
        )

        obj = get_obj_from(url)
        # print(json.dumps(obj, indent=2))  # TODO: remove
        if obj['kind'] == 'track':
            return Track(obj=obj, client=self)
        elif obj['kind'] == 'playlist':
            playlist = Playlist(obj=obj, client=self)
            playlist.clean_attributes()
            return playlist

    def _format_get_tracks_urls(self, track_ids):
        urls = []
        for start_offset in range(0, len(track_ids), self.TRACK_API_MAX_REQUEST_SIZE):
            end_offset = start_offset + self.TRACK_API_MAX_REQUEST_SIZE
            track_ids_slice = track_ids[start_offset:end_offset]
            url = self.TRACKS_URL.format(
                track_ids=','.join([str(i) for i in track_ids_slice]),
                client_id=self.client_id
            )
            urls.append(url)
        return urls

    def get_tracks(self, *track_ids):
        threads = []
        with futures.ThreadPoolExecutor() as executor:
            for url in self._format_get_tracks_urls(track_ids):
                thread = executor.submit(get_obj_from, url)
                threads.append(thread)

        tracks = []
        for thread in futures.as_completed(threads):
            result = thread.result()
            tracks.extend(result)

        tracks = sorted(tracks, key=lambda x: track_ids.index(x['id']))
        return tracks


class Track:
    __slots__ = [
        # Track Attributes
        "artwork_url",
        "artist",
        "commentable",
        "comment_count",
        "created_at",
        "description",
        "downloadable",
        "download_count",
        "download_url",
        "duration",
        "full_duration",
        "embeddable_by",
        "genre",
        "has_downloads_left",
        "id",
        "kind",
        "label_name",
        "last_modified",
        "license",
        "likes_count",
        "media",
        "permalink",
        "permalink_url",
        "playback_count",
        "public",
        "publisher_metadata",
        "purchase_title",
        "purchase_url",
        "release_date",
        "reposts_count",
        "secret_token",
        "sharing",
        "state",
        "streamable",
        "tag_list",
        "title",
        "uri",
        "urn",
        "user_id",
        "visuals",
        "waveform_url",
        "display_date",
        "monetization_model",
        "policy",
        "user",

        #extra attributes
        "album",
        "track_no",

        # Internal Attributes
        "client",
        "ready"
    ]
    STREAM_URL = "https://api.soundcloud.com/i1/tracks/{track_id}/streams?client_id={client_id}"
    def __init__(self, *, obj=None, client=None):
        if not obj:
            raise ValueError("[Track]: obj must not be None")
        if not isinstance(client, SoundcloudAPI):
            raise ValueError(f"[Track]: client must be an instance of SoundcloudAPI not {type(client)}")

        for key in self.__slots__:
            self.__setattr__(key, obj[key] if key in obj else None)

        self.client = client
        self.clean_attributes()

    def clean_attributes(self):
        username = self.user['username']
        title = self.title
        if " - " in title:
            parts = title.split("-")
            self.artist = parts[0].strip()
            self.title = "-".join(parts[1:]).strip()
        else:
            self.artist = username
#
#   Uses urllib
#
    def write_mp3_to(self, fp):
        try:
            fp.seek(0)
            stream_url = self.get_stream_url()
            fp.write(urlopen(stream_url,context=get_ssl_setting()).read())
            fp.seek(0)

            album_artwork = None
            if self.artwork_url:
                album_artwork = urlopen(
                    get_large_artwork_url(
                        self.artwork_url
                    ),context=get_ssl_setting()
                ).read()

            self.write_track_id3(fp, album_artwork)
        except (TypeError, ValueError) as e:
            eprint('File object passed to "write_mp3_to" must be opened in read/write binary ("wb+") mode')
            eprint(e)
            raise e

    def get_prog_url(self):
        for transcode in self.media['transcodings']:
            if transcode['format']['protocol'] == 'progressive':
                return transcode['url'] + "?client_id=" + self.client.client_id
        raise UnsupportedFormatError("As of soundcloud-lib 0.5.0, tracks that are not marked as 'Downloadable' cannot be downloaded because this library does not yet assemble HLS streams.")
#
#   Uses urllib
#
    def get_stream_url(self):
        prog_url = self.get_prog_url()
        url_response = get_obj_from(prog_url)
        return url_response['url']

    def write_track_id3(self, track_fp, album_artwork:bytes = None):
        try:
            audio = mutagen.File(track_fp, filename="x.mp3")
            audio.add_tags()

        # SET TITLE
            frame = mutagen.id3.TIT2(encoding=3)
            frame.append(self.title)
            audio.tags.add(frame)
        # SET ARTIST
            frame = mutagen.id3.TPE1(encoding=3)
            frame.append(self.artist)
            audio.tags.add(frame)

        # SET ALBUM
            if self.album:
                frame = mutagen.id3.TALB(encoding=3)
                frame.append(self.album)
                audio.tags.add(frame)
        # SET TRACK NO
            if self.track_no:
                frame = mutagen.id3.TRCK(encoding=3)
                frame.append(str(self.track_no))
                audio.tags.add(frame)
        # SET ARTWORK
            if album_artwork:
                audio.tags.add(
                    mutagen.id3.APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc=u'Cover',
                        data=album_artwork
                    )
                )
            audio.save(track_fp, v1=2)
            self.ready = True
            track_fp.seek(0)
            return track_fp
        except (TypeError, ValueError) as e:
            eprint('File object passed to "write_track_metadata" must be opened in read/write binary ("wb+") mode')
            raise e
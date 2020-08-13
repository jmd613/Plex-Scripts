from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import NotFound
import sys

admin_token = 'xxxxxxxxxxxxxxxxxxxx'


def getServer(name=""):
    if name == "":
        return PlexServer(token=admin_token)
    else:
        server = PlexServer(token=admin_token)
        try:
            user = server.myPlexAccount().user(name)
        except NotFound:
            return None
        return PlexServer(token=user.get_token(server.machineIdentifier))


def getLibrary(server):
    if len(server.library.sections()) == 0:
        print("Server has no libraries :(")
        sys.exit(1)
    for i, library in enumerate(server.library.sections()):
        print("%s: %s" % (i + 1, library.title))
    idx = int(input("Select Show Library: ")) - 1
    return server.library.sections()[idx]


def getShow(library):
    series = input("Show Title: ")
    search = library.search(series)
    if len(search) == 0:
        return None
    else:
        for i, show in enumerate(search):
            print("%s: %s" % (i + 1, show.title))
        idx = int(input("Select Show: ")) - 1
        return search[idx]


def getStream(streams, track_idx):
    out_stream = None
    for stream in streams:
        if stream.index == track_idx:
            out_stream = stream
            break
    return out_stream


def process_episode(episode, audio_idx, sub_idx, server):
    episode.reload()
    part = episode.media[0].parts[0]
    audio_stream = getStream(part.audioStreams(), audio_idx)
    if audio_stream is None:
        print("%s: Could not find audio track" % episode)
        return

    subtitle_stream = None
    if sub_idx >= 0:
        subtitle_stream = getStream(part.subtitleStreams(), sub_idx)
        if subtitle_stream is None:
            print("%s: Could not find subtitle track" % episode)
            return

    print("%s:" % episode)
    print("\tAudio Track: %s - %s" %
          (audio_stream.languageCode, audio_stream.title))
    if (subtitle_stream is not None):
        print("\tSubtitle Track: %s - %s" %
              (subtitle_stream.languageCode, subtitle_stream.title))
    else:
        print("\tSubtitle Track: None")

    audio_track_plex_id = audio_stream.id
    sub_track_plex_id = 0 if subtitle_stream is None else subtitle_stream.id

    server.query('/library/parts/%s?audioStreamID=%s&allParts=1' % (
        part.id, audio_track_plex_id), method=server._session.put)
    server.query('/library/parts/%s?subtitleStreamID=%s&allParts=1' % (
        part.id, sub_track_plex_id), method=server._session.put)

    print()


def process_season(season, audio_idx, sub_idx, server):
    print('\n%s\n' % season.title)
    for episode in season:
        process_episode(episode, audio_idx, sub_idx, server)


def main():
    # Usage: python3 [?username]
    username = "" if len(sys.argv) < 2 else sys.argv[1]

    plex = getServer(username)
    if plex is None:
        print("Invalid username: %s" % username)
        print("Valid Users: \nBlank for admin")
        for user in MyPlexAccount(admin_token).users():
            print(user.title)
        sys.exit(1)

    library = None
    while library is None or library.type != "show":
        library = getLibrary(plex)

    show = getShow(library)
    if show is None:
        print('Show not found!')
        sys.exit(1)

    # Select Season
    print("0: All Seasons")
    for i, season in enumerate(show.seasons()):
        print("%s: %s" % (i + 1, season.title))
    season_idx = int(input("Select Season: "))

    audio_track_id = int(input("Audio Track ID: "))
    sub_track_id = int(input("Subtitle Track ID (-1 disables): "))

    if season_idx == 0:
        for season in show.seasons():
            process_season(season, audio_track_id, sub_track_id, plex)
    else:
        season = show.seasons()[season_idx - 1]
        process_season(season, audio_track_id, sub_track_id, plex)


if __name__ == "__main__":
    main()

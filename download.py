#!/usr/bin/env python3
import requests, argparse, os, sys, json

def is_valid_name(name):
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

    for char in invalid_chars:
        if char in name:
            return False

    return True

def get_valid_name(name):
    new_name = list(name)
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '-']

    for invalid_char in invalid_chars:
        while invalid_char in new_name:
            new_name[new_name.index(invalid_char)] = '_'

    return ''.join(new_name)

def get_beatmap_url(beatmap_id):
    return 'https://osu.ppy.sh/beatmapsets/{}/download'.format(beatmap_id)

def main():
    parser = argparse.ArgumentParser(description='Download multiple beatmaps at once')
    parser.add_argument(
            'login_creds', type=str, help='File containing login credentials in json format')
    parser.add_argument('beatmap_ids', type=str, help='File of newline seperated beatmap ids')
    args = parser.parse_args()

    osu_url = 'https://osu.ppy.sh'
    dl_path = './downloaded'

    # Start osu session
    with open(args.login_creds) as loginfile:
        loginInfo = json.load(loginfile)
    session = requests.Session()
    session.post(osu_url + '/session', loginInfo)

    # Load beatmaps ids
    beatmap_ids = []
    with open(args.beatmap_ids) as beatmaps_file:
        beatmap_ids = beatmaps_file.read().split('\n')[:-1]

    if not os.path.exists(dl_path):
        os.mkdir(dl_path)

    # Download each beatmap
    for beatmap_id in beatmap_ids:
        r = session.get(get_beatmap_url(beatmap_id))

        print('{}/{}'.format(beatmap_ids.index(beatmap_id) + 1, len(beatmap_ids)))

        try:
            bm_name = r.headers['Content-Disposition'][22:-2]
            bm_path = os.path.join(dl_path, bm_name)
        except KeyError as error:
            print('Error: Beatmap {} not found'.format(beatmap_id))
            continue

        if not is_valid_name(bm_name):
            bm_path = os.path.join(dl_path, get_valid_name(bm_name))

        with open(bm_path, 'wb') as response:
            response.write(r.content)

if __name__ == '__main__':
    main()

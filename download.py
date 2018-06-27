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

def get_beatmapset_url(beatmapset_id):
    return 'https://osu.ppy.sh/beatmapsets/{}/download'.format(beatmapset_id)

def main():
    parser = argparse.ArgumentParser(description='Download multiple beatmap sets at once')
    parser.add_argument(
            'login_creds', type=str, help='File containing login credentials in json format')
    parser.add_argument('beatmapset_ids', type=str, help='File of newline seperated beatmap set ids')
    args = parser.parse_args()

    osu_url = 'https://osu.ppy.sh'
    dl_path = './downloaded'

    # Start osu session
    with open(args.login_creds) as loginfile:
        loginInfo = json.load(loginfile)
    session = requests.Session()
    session.post(osu_url + '/session', loginInfo)

    # Load beatmapsets ids
    beatmapset_ids = []
    with open(args.beatmapset_ids) as beatmapsets_file:
        beatmapset_ids = beatmapsets_file.read().split('\n')[:-1]

    if not os.path.exists(dl_path):
        os.mkdir(dl_path)

    # Download each beatmapset
    for beatmapset_id in beatmapset_ids:
        r = session.get(get_beatmapset_url(beatmapset_id))

        print('{}/{}'.format(beatmapset_ids.index(beatmapset_id) + 1, len(beatmapset_ids)))

        try:
            bm_name = r.headers['Content-Disposition'][22:-2]
            bm_path = os.path.join(dl_path, bm_name)
        except KeyError as error:
            print('Error: Beatmap set {} not found'.format(beatmapset_id))
            continue

        if not is_valid_name(bm_name):
            bm_path = os.path.join(dl_path, get_valid_name(bm_name))

        with open(bm_path, 'wb') as response:
            response.write(r.content)

if __name__ == '__main__':
    main()

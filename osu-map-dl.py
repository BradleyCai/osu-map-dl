#!/usr/bin/env python3
import requests, argparse, os, sys, json

def get_beatmapset_id(osu_url, api_key, beatmap_id):
    payload = {'k': api_key, 'b': beatmap_id}
    r_json = requests.post(osu_url + '/api/get_beatmaps', data=payload).json()
    if r_json == []:
        return None

    return r_json[0]['beatmapset_id']

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
    parser.add_argument(
        'beatmapset_ids', type=str, help='File of newline seperated beatmap set ids')
    parser.add_argument(
        '-b', '--use_beatmap_ids', action='store_true',
        help='Use beatmap ids instead of beatmap set ids')
    args = parser.parse_args()

    osu_url = 'https://osu.ppy.sh'
    dl_path = './downloaded'

    # Start osu session
    with open(args.login_creds) as loginfile:
        login_info = json.load(loginfile)
    session = requests.Session()
    session.post(osu_url + '/session', login_info)

    # Load beatmapsets ids
    file_lines = []
    with open(args.beatmapset_ids) as beatmapsets_file:
        file_lines = beatmapsets_file.read().split('\n')[:-1]

    beatmapset_ids = []
    if args.use_beatmap_ids:
        for line in file_lines:
            id = get_beatmapset_id(osu_url, login_info['api_key'], line)
            if id != None:
                beatmapset_ids.append(id)
    else:
        beatmapset_ids = file_lines

    if not os.path.exists(dl_path):
        os.mkdir(dl_path)

    # Download each beatmapset
    for beatmapset_id in beatmapset_ids:
        r = session.get(get_beatmapset_url(beatmapset_id))

        try:
            bm_name = r.headers['Content-Disposition'][22:-2]
            bm_path = os.path.join(dl_path, bm_name)
            print('{}/{} {}'.format(
                beatmapset_ids.index(beatmapset_id) + 1, len(beatmapset_ids), bm_name))
        except KeyError as error:
            print('Error: Beatmap set {} not found'.format(beatmapset_id))
            continue

        if not is_valid_name(bm_name):
            bm_path = os.path.join(dl_path, get_valid_name(bm_name))

        with open(bm_path, 'wb') as response:
            response.write(r.content)

if __name__ == '__main__':
    main()

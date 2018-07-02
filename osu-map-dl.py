#!/usr/bin/env python3
import requests, argparse, os, sys, json, re, time

def get_beatmapset_id(api_key, beatmap_id):
    osu_url = 'https://osu.ppy.sh'
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
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

    for invalid_char in invalid_chars:
        while invalid_char in new_name:
            new_name[new_name.index(invalid_char)] = '_'

    return ''.join(new_name)

def parse_map_url(url, api_key):
    # If url matches new website format
    match = re.search('\/beatmapsets\/(\d+)(?:#\w+\/)?(\d*)', url)
    if match:
        return match.group(1)

    # If url matches old website beatmap set format
    match = re.search('\/s\/(\d+)', url)
    if match:
        return match.group(1)

    # If url matches old website beatmap format
    match = re.search('\/b\/(\d+)', url)
    if match:
        return get_beatmapset_id(api_key, match.group(1))

    return None

def get_beatmapset_url(beatmapset_id):
    return 'https://osu.ppy.sh/beatmapsets/{}/download'.format(beatmapset_id)

def main():
    # Set up cli
    parser = argparse.ArgumentParser(description='Download multiple beatmap sets at once')
    parser.add_argument(
        'login_creds', type=str, help='File containing login credentials in json format')
    parser.add_argument(
        'maps_filename', type=str, help='Filename of the list of beatmap set urls to download')
    parser.add_argument(
        '-r', '--use_raw_ids', action='store_true',
        help='Use a file of beatmap set id numbers instead of links')
    args = parser.parse_args()
    dl_path = os.path.splitext(args.maps_filename)[0]

    # Start osu session
    osu_url = 'https://osu.ppy.sh'

    with open(args.login_creds) as loginfile:
        login_info = json.load(loginfile)
    session = requests.Session()
    session.post(osu_url + '/session', login_info)

    # Load beatmapsets ids
    beatmapset_ids = []
    with open(args.maps_filename) as beatmapsets_file:
        for line in beatmapsets_file:
            if args.use_raw_ids:
                beatmapset_id = line
            else:
                beatmapset_id = parse_map_url(line, login_info['api_key'])

            if beatmapset_id != None:
                beatmapset_ids.append(beatmapset_id)

    if not os.path.exists(dl_path):
        os.mkdir(dl_path)

    # Download each beatmapset
    for i, beatmapset_id in enumerate(beatmapset_ids):
        r = session.get(get_beatmapset_url(beatmapset_id))
        curr_str = '({}/{})'.format(i + 1, len(beatmapset_ids))

        try:
            bm_name = r.headers['Content-Disposition'][22:-2]
            bm_name = bm_name if is_valid_name(bm_name) else get_valid_name(bm_name)
            bm_path = os.path.join(dl_path, bm_name)

            with open(bm_path, 'wb') as response:
                response.write(r.content)

            print('{} {}'.format(curr_str, bm_name))
        except KeyError as error:
            print('Error: Beatmap set "({}) {}" not found'.format(curr_str, beatmapset_id))

if __name__ == '__main__':
    main()

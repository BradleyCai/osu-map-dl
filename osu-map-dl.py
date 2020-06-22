#!/usr/bin/env python3
import requests, urllib, argparse, os, sys, json, re, time

def get_beatmapset_id(api_key, beatmap_id):
    osu_url = 'https://osu.ppy.sh'
    payload = {'k': api_key, 'b': beatmap_id}

    request = requests.post(osu_url + '/api/get_beatmaps', data=payload)
    request.raise_for_status()

    r_json = request.json()
    if r_json == []:
        return None
    else:
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
    return 'https://osu.ppy.sh/beatmapsets/{}'.format(beatmapset_id)

def main():
    # Set up cli
    parser = argparse.ArgumentParser(description='Download multiple beatmap sets at once')
    parser.add_argument('--login_creds', type=str, nargs='?', default='login.json',
        help='File containing login credentials in json format. Defaults to \'login.json\'')
    parser.add_argument('--api_key', type=str, nargs='?', default='api_key.json',
        help='File containing api key in json format. Defaults to \'api_key.json\'')
    parser.add_argument('maps_filename', type=str,
        help='Filename of the list of beatmap set urls to download')
    parser.add_argument('-r', '--use_raw_ids', action='store_true',
        help='Use a file of beatmap set id numbers instead of links')
    parser.add_argument('--download_timeout', type=float, nargs='?', default=0.5,
        help='The timeout inbetween downloading beatmapsets in seconds. Default is 0.5 second')
    args = parser.parse_args()

    osu_url = 'https://osu.ppy.sh'
    with open(args.api_key) as api_key_file:
        api_key = json.load(api_key_file)
    with open(args.login_creds) as loginfile:
        login_info = json.load(loginfile)

    # initiate session
    session = requests.Session()
    session.get(osu_url + '/home')

    # set special request header information and login
    login_info['_token'] = session.cookies.get('XSRF-TOKEN')
    home_req = requests.Request('POST', osu_url + '/session', data=urllib.parse.urlencode(login_info).replace('%2B', '+'))
    prepped = session.prepare_request(home_req)
    prepped.headers['Host'] = 'osu.ppy.sh'
    prepped.headers['Origin'] = osu_url
    prepped.headers['Referer'] = osu_url + '/home'
    prepped.headers['X-CSRF-Token'] = login_info['_token']
    prepped.headers['Content-Type'] = 'application/x-www-form-urlencoded'
    session.send(prepped)

    # Load beatmapsets ids
    beatmapset_ids = []
    with open(args.maps_filename) as beatmapsets_file:
        for line in beatmapsets_file:
            if args.use_raw_ids:
                beatmapset_id = line
            else:
                beatmapset_id = parse_map_url(line, api_key['api_key'])

            if beatmapset_id != None:
                beatmapset_ids.append(beatmapset_id)
            else:
                print(('Warning: The map url "{}" was '
                    'not recognized as a valid map link').format(line[:-1]))

    dl_path = os.path.splitext(args.maps_filename)[0]
    if not os.path.exists(dl_path):
        os.mkdir(dl_path)

    # Download each beatmapset
    for i, beatmapset_id in enumerate(beatmapset_ids):
        map_progress_str = '{}/{}'.format(i + 1, len(beatmapset_ids))
        str_pad = '    '
        print('Downloading map ' + map_progress_str)

        beatmapset_url = get_beatmapset_url(beatmapset_id)
        session.headers.update({'referer': beatmapset_url})
        r = session.get(beatmapset_url + '/download')
        try:
            bm_name = r.headers['Content-Disposition'][22:-2]
            bm_name = bm_name if is_valid_name(bm_name) else get_valid_name(bm_name)
            bm_path = os.path.join(dl_path, bm_name)

            with open(bm_path, 'wb') as bm_file:
                bm_file.write(r.content)
            print(str_pad + 'Map {} downloaded to {}'.format(i + 1, bm_path))
        except KeyError as error:
            print(str_pad + 'Error: Beatmap set {} was not found'.format(beatmapset_id))

        time.sleep(args.download_timeout)

if __name__ == '__main__':
    main()

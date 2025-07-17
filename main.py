import os
import time
from flask import Flask, jsonify
import requests
import yaml

app = Flask(__name__)

LUA_GLOBALS_URL = "https://raw.githubusercontent.com/Roblox/creator-docs/main/content/en-us/reference/engine/globals/LuaGlobals.yaml"
ROBLOX_GLOBALS_URL = "https://raw.githubusercontent.com/Roblox/creator-docs/main/content/en-us/reference/engine/globals/RobloxGlobals.yaml"
DATATYPES_API_URL = "https://api.github.com/repos/Roblox/creator-docs/contents/content/en-us/reference/engine/datatypes"
LIBRARIES_API_URL = "https://api.github.com/repos/Roblox/creator-docs/contents/content/en-us/reference/engine/libraries"

CACHE_DURATION = 30 * 24 * 60 * 60
cache = {
    'data': None,
    'timestamp': 0,
}


def fetch_names_from_yaml(url):
    response = requests.get(url)
    response.raise_for_status()
    yaml_data = yaml.safe_load(response.text)
    properties = yaml_data.get('properties', [])
    functions = yaml_data.get('functions', [])
    return [
        item.get('name') for item in properties + functions if 'name' in item
    ]


def fetch_yaml_filenames(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    files = response.json()
    yaml_files = [
        file['name'] for file in files
        if file['type'] == 'file' and file['name'].endswith('.yaml')
    ]
    return [name[:-5] for name in yaml_files]  # strip '.yaml'

def update_cache():
    lua_names = fetch_names_from_yaml(LUA_GLOBALS_URL)
    roblox_names = fetch_names_from_yaml(ROBLOX_GLOBALS_URL)
    datatype_names = fetch_yaml_filenames(DATATYPES_API_URL)
    library_names = fetch_yaml_filenames(LIBRARIES_API_URL)

    combined = set(lua_names + roblox_names + datatype_names + library_names)
    filtered = [name for name in combined if not name.startswith("RBX")]
    cache['data'] = sorted(filtered)
    cache['timestamp'] = time.time()

def is_cache_stale():
    return (time.time() -
            cache['timestamp']) > CACHE_DURATION or cache['data'] is None


@app.route('/', methods=['GET'])
def get_all_names():
    try:
        if is_cache_stale():
            update_cache()
        return jsonify(cache['data'])
    except requests.RequestException as e:
        return jsonify({
            'error': 'Failed to fetch data',
            'details': str(e)
        }), 500
    except yaml.YAMLError as e:
        return jsonify({
            'error': 'Failed to parse YAML',
            'details': str(e)
        }), 500


if __name__ == '__main__':
    try:
        update_cache()
    except Exception as e:
        print(f"Warning: Failed to pre-cache data on startup: {e}")
    app.run(host='0.0.0.0', port=80)

import os
import time
import json
import requests
import yaml

LUA_GLOBALS_URL = "https://raw.githubusercontent.com/Roblox/creator-docs/main/content/en-us/reference/engine/globals/LuaGlobals.yaml"
ROBLOX_GLOBALS_URL = "https://raw.githubusercontent.com/Roblox/creator-docs/main/content/en-us/reference/engine/globals/RobloxGlobals.yaml"
DATATYPES_API_URL = "https://api.github.com/repos/Roblox/creator-docs/contents/content/en-us/reference/engine/datatypes"
LIBRARIES_API_URL = "https://api.github.com/repos/Roblox/creator-docs/contents/content/en-us/reference/engine/libraries"

CACHE_DURATION = 30 * 24 * 60 * 60
CACHE_FILE = "cache.json"
OUTPUT_FILE = "output.json"


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {'data': None, 'timestamp': 0}

    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return {'data': None, 'timestamp': 0}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def fetch_names_from_yaml(url):
    response = requests.get(url)
    response.raise_for_status()
    yaml_data = yaml.safe_load(response.text)
    properties = yaml_data.get('properties', [])
    functions = yaml_data.get('functions', [])
    return [item.get('name') for item in properties + functions if 'name' in item]


def fetch_yaml_filenames(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    files = response.json()
    yaml_files = [
        file['name'] for file in files
        if file['type'] == 'file' and file['name'].endswith('.yaml')
    ]
    return [name[:-5] for name in yaml_files]  # strip ".yaml"


def update_cache(cache):
    lua_names = fetch_names_from_yaml(LUA_GLOBALS_URL)
    roblox_names = fetch_names_from_yaml(ROBLOX_GLOBALS_URL)
    datatype_names = fetch_yaml_filenames(DATATYPES_API_URL)
    library_names = fetch_yaml_filenames(LIBRARIES_API_URL)

    combined = set(lua_names + roblox_names + datatype_names + library_names)
    filtered = [name for name in combined if not name.startswith("RBX")]

    cache['data'] = sorted(filtered)
    cache['timestamp'] = time.time()
    return cache


def is_cache_stale(cache):
    return (time.time() - cache['timestamp']) > CACHE_DURATION or cache['data'] is None


if __name__ == "__main__":
    cache = load_cache()

    if is_cache_stale(cache):
        print("Cache is stale — updating...")
        cache = update_cache(cache)
        save_cache(cache)
    else:
        print("Using cached data.")

    # Write output to file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(cache['data'], f, indent=2)

    print(f"Output written to {OUTPUT_FILE}")

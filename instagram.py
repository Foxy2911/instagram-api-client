from collections import namedtuple
from distutils.command.config import config
from encodings import utf_8
import datetime
import json
import os.path
import codecs
import configparser
from instagram_private_api import (Client, ClientError, ClientLoginError,ClientCookieExpiredError, ClientLoginRequiredError,__version__ as client_version)

def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')

def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object

def main():
    print("trying to start instagram account wrapper")
    #ask all the user for info
    if os.path.exists("configurations.ini") == False:
        get_info()
    #login 
    api = login()

    print(api.android_release)
    print(api.direct_v2_inbox())
    #save the response
    print("Done")

def get_info():
    config_file = configparser.ConfigParser()
    #ask all the user for info
    username = input("username: ")
    password = input("password: ")
    # ADD SECTION
    config_file.add_section("InstagramAPI")
    # ADD SETTINGS TO SECTION
    config_file.set("InstagramAPI", "username", username)
    config_file.set("InstagramAPI", "password", password)
    # SAVE CONFIG FILE
    with open(r"configurations.ini", 'w') as configfileObj:
        config_file.write(configfileObj)
        configfileObj.flush()
        configfileObj.close()
    print("Config file 'configurations.ini' created")


def login():
    try:
        #load info from config file
        # PRINT FILE CONTENT
        config = configparser.ConfigParser()
        config.read("configurations.ini")
        print("Content of the config file are:\n")
        username = config["InstagramAPI"]["username"]
        password = config["InstagramAPI"]["password"]

        print('Client version: {0!s}'.format(client_version))

        print()
        if os.path.exists("cache_settings.json") == False:
            print("cached_settings not found")
            api = Client(username, password)
            cache_settings = api.settings
            with open("cache_settings.json", 'w') as outfile:
                json.dump(cache_settings, outfile, default=to_json)
                print('SAVED: {0!s}'.format("cache_settings.json"))
        else:
            print("login with cached settings")
            with open("cache_settings.json") as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Reusing settings: {0!s}'.format("cache_settings.json"))

            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(username, password, settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))
    
      # Login expired
        # Do relogin but use default ua, keys and such
        api = Client(username, password, device_id=device_id)
        cache_settings = api.settings
        with open("cache_settings.json", 'w') as outfile:
            json.dump(cache_settings, outfile, default=to_json)
            print('SAVED: {0!s}'.format("cache_settings.json"))

    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)

    # Show when login expires
    cookie_expiry = api.cookie_jar.auth_expires
    print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))

    return api


if __name__ == "__main__":
    main()
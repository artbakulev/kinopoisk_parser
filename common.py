import json


def get_set_from_json(json_filename, key, nested=False):
    with open(json_filename) as f:
        json_body = json.load(f)
    s = set()
    if nested:
        for item in json_body:
            for json_val in item[key]:
                s.add(json_val)
    else:
        for item in json_body:
            s.add(item[key])
    print("got {} {} from {}".format(len(s), key, json_filename))
    return s

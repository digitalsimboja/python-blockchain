import json


def object_to_dict(obj):
    # Convert the object to a dictionary
    # You will need to add code here to convert the object's attributes to dictionary keys
    dict = {
        'id': obj.id,
        'block': obj.block,
        'timestamp': obj.timestamp,
        'nonce': obj.nonce,
        'prev_hash': obj.prev_hash,
        'root_hash': obj.root_hash,
        'hash': obj.hash,
    }
    return dict


def serialize(objects):
    dicts = [object_to_dict(obj) for obj in objects]

    # Serialize the list of dictionaries to a JSON string
    json_string = json.dumps(dicts, sort_keys=True)

    return (json_string)

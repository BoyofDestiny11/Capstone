import ujson as json

def load():
    try:
        with open('save.json', 'r') as f:
            return json.load(f)
    except:
        return {"schedule": [],
                "amounts": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                "last_dose_taken": True,
                "init_time": 0}

def save(data):
    try:
        with open('save.json', 'w') as f:
            json.dump(data, f)
    except:
        raise ExceptionGroup("File could not be saved.")


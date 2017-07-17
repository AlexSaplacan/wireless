def init():

    # data handling

    import os
    import json

    json_path = os.path.join(os.path.dirname(__file__), "configs.json")

    global data
    with open(json_path) as data_file:
        data = json.load(data_file)

    # #########################################

    global thumbs
    thumbs = {}

    # to avoid loops
    global switch
    switch = False

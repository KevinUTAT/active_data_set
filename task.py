import json
import os


class Task(object):

    def __init__(self, json_file):
        self.json_doc = json.load(json_file)
        self.data_location = self.json_doc["Data Location"]
        self.yaml_location = self.json_doc["Yaml Location"]
        self.finished_data = self.json_doc["Finished Data"]
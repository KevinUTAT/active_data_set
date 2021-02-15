import json
import os


class Task(object):

    def __init__(self, json_dir):
        self.dir = json_dir
        with open(json_dir, 'r') as json_file:
            self.json_doc = json.load(json_file)
        self.data_location = self.json_doc["Data Location"]
        self.yaml_location = self.json_doc["Yaml Location"]
        self.finished_data = self.json_doc["Finished Data"]

    
    # mark a data as finished
    # add to finished data and update file
    def finish_data(self, data_name):
        if data_name in self.finished_data:
            return
        self.finished_data.append(data_name)
        self.json_doc["Finished Data"] = self.finished_data
        with open(self.dir, 'w') as out_json:
            out_json.write(json.dumps(self.json_doc, indent=4))


    # remove marking of finished for a data
    def mark_as_unfinished(self, data_name):
        if data_name not in self.finished_data:
            return
        self.finished_data.remove(data_name)
        self.json_doc["Finished Data"] = self.finished_data
        with open(self.dir, 'w') as out_json:
            out_json.write(json.dumps(self.json_doc, indent=4))


    def __del__(self):
        # when destroyed, update the file
        self.json_doc["Data Location"] = self.data_location
        self.json_doc["Yaml Location"] = self.yaml_location
        self.json_doc["Finished Data"] = self.finished_data
        with open(self.dir, 'w') as out_json:
            out_json.write(json.dumps(self.json_doc, indent=4))
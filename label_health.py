import os
from ADS_config import (label_table, modification_list, IMG_FOLDER, 
                        IMG_EXT, LEBEL_FOLDER, DEFAULT_CLS)


def check_for_missing_newline(date_dir):
    error_list = []
    for label in os.listdir(date_dir + LEBEL_FOLDER):
        with open(date_dir + LEBEL_FOLDER \
            + "/" + label) as label_file:
            for line in label_file:
                line_segs = line.split()
                if len(line_segs) > 5:
                    error_list.append(f"Line error in: {label}")
                    break
    return error_list
import os
from ADS_config import (label_table, modification_list, IMG_FOLDER, 
                        IMG_EXT, LEBEL_FOLDER, DEFAULT_CLS)


# Check for a problem where new line is missing 
def check_for_missing_newline(data_dir):
    error_list = []
    for label in os.listdir(data_dir + LEBEL_FOLDER):
        with open(data_dir + LEBEL_FOLDER \
            + "/" + label) as label_file:
            for line in label_file:
                line_segs = line.split()
                if len(line_segs) > 5:
                    error_list.append(f"Line error in: {label}")
                    break
    return error_list


# check for label out of img range
# have it accurate to 0.01%, smaller then a pixel in 8k
def check_out_of_range(data_dir):
    error_list = []
    label_list = []
    for label in os.listdir(data_dir + LEBEL_FOLDER):
        with open(data_dir + LEBEL_FOLDER \
            + "/" + label) as label_file:
            for i, line in enumerate(label_file):
                error_count = 0
                line_segs = line.split()
                # check left
                left = float(line_segs[1]) - (float(line_segs[3])/2)
                if left < -0.0001:
                    error_list.append(f"{label}({i}): Out-of-range left")
                    error_count += 1
                # check right
                right = float(line_segs[1]) + (float(line_segs[3])/2)
                if right > 1.0001:
                    error_list.append(f"{label}({i}): Out-of-range right")
                    error_count += 1
                # check top
                top = float(line_segs[2]) - (float(line_segs[4])/2)
                if top < -0.0001:
                    error_list.append(f"{label}({i}): Out-of-range top")
                    error_count += 1
                # check bottom
                bottom = float(line_segs[2]) + (float(line_segs[4])/2)
                if bottom > 1.0001:
                    error_list.append(f"{label}({i}): Out-of-range bottom")
                    error_count += 1
                if error_count > 0:
                    label_list.append(label)
    return error_list, label_list

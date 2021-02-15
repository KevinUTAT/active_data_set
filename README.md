[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
# Intro
This little tool is build to manage data sets for learning. It currently supports COCO style annotation and its tested with some of my YOLO projects that you can find here: [RPANet](https://github.com/KevinUTAT/RPANet), [Surviver.IO](https://github.com/KevinUTAT/surviver_dot_IO) \
The focus of this tool is *active learning*, by providing simple work flow of editing existing annotations that maybe generated through active learning. \
The current build supports loading a existing datasets with images and labels and allows you to edit, delete and add new annotations.\
The tools is light weight and build with Python and PySide2 framework.
# Change log
### 2021-02-07
- Task system are functioning in a bare bone manner.
- Now task will track all of finished data so you can pick up later
- Data background turn grey if its "finished"
### 2021-01-30
- Introducing Task system. A task is annotation flow that keep track of you progress as well.
- Add the new task window to generating a new Task
### 2021-01-10
- Create this repo and move the tool form [Surviver.IO](https://github.com/KevinUTAT/surviver_dot_IO).
- Small changes to make the tool independent, including disabling generating active data from video.
# How to run
First install python >= 3.8 or Anaconda and install dependency in requirements.txt
```
conda create --name <envname> --file requirements.txt
```
If ypu don't want to use conda, you need to modify requirements.txt to match pip install. \
Once dependencies are installed, run the tool:
```
python activeDS.py
```
# How to start
## Work with a data folder
You will need a folder with your data organized as follow:
```
You_data_folder |
                |_ images |
                          |_ data_image_01.png
                          |_ data_image_02.png
                          |_ ... ...
                |_ labels |
                          |_ data_image_01.txt
                          |_ data_image_02.txt
                          |_ ... ...
```
Go to *Load* -> *Active learning output* to load such folder. You label are expected to be in COCO format:
```
<class number>, <center X>, <center Y>, <width>, <height>
... ...
```
## Work with a task
You can open a existing task by open the JSON task file by *Task* -> *Open* \
Or start a new task using the new task wizard: *Task* -> *New* \
When in task, opening a data will automatically mark it as *finished* and the data background turns grey. Double click a data to mark it as *unfinished* 
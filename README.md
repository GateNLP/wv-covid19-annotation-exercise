# wv-covid19-annotation-exercise

Notes, software, configuration for the WV Covid19 Annotation Exercise

## Note/Documents:

* About label-studio: [label-studio/README.md](label-studio/README.md)
* Annotation guidelines:
  * https://gate.ac.uk/wiki/wv-covid19/annotation-guidelines.html


## Final procedure to set everything up 

* Install a recent python 3.x (ideally, Anaconda)
* Create a Python environment and activate: 
  * `conda create -n labelstudio`
  * `conda activate labelstudio`
* Install labelstudio:
  * The label-studio software has been heavily modified specifically for this we need to use the version in
  * https://github.com/GateNLP/label-studio-patched
  * To install from there, changine into cloned repo and do `pip install -e .` 
* Install the requirements for the programs in here:
  * `pip install -r requirements.txt`
* All the python programs show detailled usage information when invoked with the option `--help`
* Additional documentation is in the python file at the top in the docstring
* NOTE: annotator ids in file names are two-digit numbers, e.g. 08, set numbers are thre digit numbers e.g. 003
* Prepare the data. All commands are assumed to be run from the root dir of this repository:
  * use the program `python/prepare-split-data.py`
  * This shuffles the input data, splits it up into files with an equal number of items and stores the files with a common path prefix
  * e.g. `./python/prepare-split-data.py data/Poynter_Dataset.json.gz sets/data -s 25`
    * creates as many files with 25 items each as possible and stores them with names like `sets/data_set013.json`
  * eyeball the files created for each annotator, e.g. using the command `json_pp < infile | less`
* Assign sets to annotators for the first annotation: for this, no random shuffling is needed, we just need to copy the data from 
  the original split files and note in each item which annotator it is assigned to
  * use the program `python/prepare-assign-data.py`
  * e.g. `./python/prepare-assign-data.py sets/data label-studio/data 0 15`
    * creates 15 files like `label-studio/data_set008_ann08.json` by taking 15 sets starting with set 0 
* Prepare the label-studio projects:
  * NOTE: a new project directory has to be created for each new input file per annotator. Use a good naming scheme. Keep the project
    directories for completed/finished annotations by one annotator for one input file around: even if the retrieve program has a bug
    we can thus always access the original full data!
  * use the program python/prepare-labelstudio.py to create a whole bunch of projects from a bunch of files created with `prepare-assign-data.py`
  * However, can also run this individually (see next main item)
  * This creates one directory for running a server for each of the k annotators, creates the necessary config data and imports 
    the data for that annotator
  * option `--help` shows usage information: `./python/prepare-labelstudio.py --help`
  * `./python/prepare-labelstudio.py -k 10 label-studio/data label-studio/project_round1`
* Or, prepare each label-studio project separately by running the label-studio command directly:
  * e.g. `label-studio init -l label-studio/tmpl_config.xml -i label-studio/data_set008_ann08.json --input-format json project_round1_08`
    * use the file `label-studio/tmpl_config.xml` for the label config
    * read the data from `label-studio/data_set008_ann08.json` so the data prepared for annotator 08
    * store all the stuff in the server project directory `project_round1_08`
    * project name contains info about the annotation round in progress for annotator 08
* Start the label-studio projects: 
  * ideally, use a screen session for each project
  * there is a bug, even though the correct port gets configured for each project, labelstudio does not use it, so the port
    needs to get specified manually for each server
  * in each screen session, start a project using the command:
  * `label-studio start -p PORTNR PROJECTDIR`
  * e.g. `label-studio start -p 9000 label-studio/project_round1_00` 
  * e.g. `label-studio start -p 9001 label-studio/project_round1_01`
  * These will get proxied to https://wv-ann-00.services.gate.ac.uk/ https://wv-ann-01.services.gate.ac.uk/ etc
* Annotate! Each annotator should work on his own server (on a separate port)
   which manages his set of items
  * When navigating to the server URL, if the web page does not show an item to annotate, click "Labeling" in the top menu
  * When the web page appears to hang, restart the browser!
  * please do not skip items but annotate each item in sequence
  * to copy-paste from the shown text, press Ctrl-C while the mouse button is still pressed when selecting the text
  * to open the link shown in the annotation area, use right-click then "open in tab/window", directly clicking does NOT WORK! 
* Retrieve the data for annotators that have finished
  * use the program python/retrieve-annotated.py
  * e.g. `./python/retrieve-annotated.py label-studio/project_round1_00 label-studio/data_fromann00.json 0`
  * The program does not automatically retrieve the annotator id from the project name, it must be specified as the third parameter
  * The program will report how many annotations it has found and if there were any problems, maybe not all items have been annotated
* Once all annotators have finished and the corresponding files have been created, they can be used as input to re-assign 
  the same data to the same or a different number of annotators (but annotator ids still have to match)
  * use the program python/reassign.py
  * the program needs a list of annotation files retrieved and a list of annotator ids to assign to
  * the list of annotation files retrieved may not include files from all annotators
  * the list of annotators to assign to may not include all annotators
  * e.g. `./python/reassign --infiles label-studio/data_fromann00.json label-studio/data_fromann02.json label-studio/data_fromann03 .json --annotators 2 3 --outpref reassigned`
  * this would use the retrieved annotations from annotators 0, 2 and 3 and randomly reassign as equal as possible to  annotators 2 and 3
  * it will create files `reassigned_ann02.json` and `reassigned_ann03.json`
* Once annotators have annotated again, retrieve their annotations again to a new set of files (same as above)
* To assess IAA, run the ./python/agreement.py program on those files.
  * e.g. `./python/agreement.py  --infiles label-studio/retrieved_round2_ann01.json label-studio/retrieved_round2_ann02.json--outcsv agreement.csv`


# GNN Techniques from the paper `Information extraction in handwritten historical logbooks`

In this repository you will find the original code from the paper `Information extraction in handwritten historical logbooks` for the use of Graph Neural Networks (GNNs) to extract information from structured documents.

## Getting started

First, you will need to install the dependencies using pip. It's recommended to create a virtual environment first.

```
pip install -r requirements.txt
```

## Initial graph creation

For initial graph creation, we will modify and execute the provided sample launchers.

```
cd data/launchers/
./launch_HisClima_JeannetteAndAlbatross_GT.sh
```

First, you will need to modify the `data_path` variable, which should point to the folder PAGE files. The parameters for each graph have been set according to the original paper's instructions.

Also, the `path` variable is where the created graphs will be saved.

| :warning: WARNING          |
|:---------------------------|
| The code in these scripts, particularly in ``data/create_graphs.py`` is not designed for efficiency. This code can be highly improved. |


## Model training

To train the models that we just created, just execute the script in the main launchers folder:

```
cd launchers
./launch_Hisclima_AlbatrossAndJeannette_GT_NC.sh
```

The parameters for each model have been set according to the original paper's instructions. This script will train the four necessary models based on GNN (ROW, COL, HEADERS and SPAN).

The `data_path` variable will point to the created and preprocessed graphs.
You will need to modify the `test_lst, train_lst, val_lst` variables so they point to a plain file with the list of files by partitions with the following format:

```
vol003_139_0.xml
vol003_116_0.xml
vol003_076_0.xml
vol003_061_0.xml
...
```

| :warning: WARNING          |
|:---------------------------|
| The `name_data` variables by default point to the graph created for each model with the script for creating graphs from the previous step. If you modify any parameters when modifying the initial graphs, you will need to modify this variable accordingly. |

The results will be saved in a `results.txt` file with the posterior log-probabilities.

## Using the results for information extraction


Once we have the trained models, the remaining task is to extract the information by joining all the results.
The first step will be to run the span model and then extract the information:

```
cd information_extraction
./launch_span_AlbatrossAndJeannette.sh
```

In the file `launch_span_AlbatrossAndJeannette.sh` you will need to ensure that `path_results` points to the results obtained by the SPAN model and `files_to_use` points to the file with the list of files.
Additionally, `path_coords` is a file that contains the textual information and its coordinates, previously extracted by a HTR model and line detection, for instance.

The format of this file is as follows:
```
{filename}.{id_line} {text_line}  Coords:( {coords_line} )
```

Then we will run the script `headers.py`
```
python headers.py
```

This script will train a LM to help us classify the headers by their textual content. For this, two files are expected in the `headers/AlbatrossAndJeannette` folder. `colHeaders.txt` contains all possible train headers and `colHeadersUniq.txt` contains the same but separated into classes by '#'. The result will be saved in `headers/AlbatrossAndJeannette/train/models/lm.pkl` by default.

*The content from these txt's is previously made by hand, since it depends on the corpus.*

Finally, we will modify the pertinent variables, similar to the previous script and we will be able to execute the main script:

```
launch_IE_AlbatrossAndJeannetteGT.sh/.
```

This will create a file called `hyp_file.txt` with the following format:

```
{image_name} {probability} [{content col_header}]|{row_header} {content}
```

For example:
```
Albatross_vol042of055-091-0 1.0 WIND DIRECTION|table1_7 WSW
```

This tells us that in the image `Albatross_vol042of055-091-0` in table 1, row 7, with header `WIND DIRECTION`, the content is `WSW`.
With the GNN, the probability will always be `1.0`.


## Evaluation

To evaluate, simply use the provided evaluation toolkit (`evaluateIE.o`) and modify `path_IE_GT` to point to the GT file for evaluation, which has the same format as `hyp_file.txt` but without the probability column:


```
path_IE_GT=GT_IE_test.txt
evaluateIE.o ${path_hyp_file} ${path_IE_GT}
mv FN.txt ${path_hyp_file}/FN.txt
mv FP.txt ${path_hyp_file}/FP.txt
```

## Cite us!

If you want to cite us in one of your works, please use the following citation.

```latex
@article{PRIETO2023128,
title = {Information extraction in handwritten historical logbooks},
journal = {Pattern Recognition Letters},
volume = {172},
pages = {128-136},
year = {2023},
issn = {0167-8655},
doi = {https://doi.org/10.1016/j.patrec.2023.06.008},
url = {https://www.sciencedirect.com/science/article/pii/S016786552300185X},
author = {Jose Ramón Prieto and José Andrés and Emilio Granell and Joan Andreu Sánchez and Enrique Vidal},
keywords = {Structured handwritten documents, Information extraction, Neural networks},
}
```

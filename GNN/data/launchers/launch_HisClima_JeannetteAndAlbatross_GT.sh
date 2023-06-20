#!/usr/bin/env bash
cd ..
path=graphs
data_path="/data/HisClima/HisClimaProd/DLA/HisClima_0/all_corregido"
hisclima=true
mkdir ${path}/graphs_preprocessed
###Normal, for HEADERS 
minradio=0
min_num_neighrbors=10
weight_radius_w=0
weight_radius_h=0
j_h=1
j_w=1
###
max_width_line=0.5
name_path="k${min_num_neighrbors}_wh${weight_radius_h}ww${weight_radius_w}jh${j_h}jw${j_w}_maxwidth${max_width_line}_minradio${minradio}"
dir_dest=${path}/graph_${name_path}
dir_dest_processed=${path}/graphs_preprocessed/graph_${name_path}
python create_graphs.py --dir ${data_path} --dir_dest ${dir_dest} --minradio ${minradio} --min_num_neighbours ${min_num_neighrbors} \
--weight_radius_w ${weight_radius_w} --weight_radius_h ${weight_radius_h} --mult_punct_w ${j_h} --mult_punct_h ${j_w} \
--max_width_line ${max_width_line} --hisclima "true" --do_spans "false" --data_path_tablelabel ""  --reading_order "false"
python preprocess.py ${dir_dest} ${dir_dest_processed}

## COL
minradio=0.1
min_num_neighrbors=10
weight_radius_w=4
weight_radius_h=0 
j_h=1
j_w=1
name_path="k${min_num_neighrbors}_wh${weight_radius_h}ww${weight_radius_w}jh${j_h}jw${j_w}_maxwidth${max_width_line}_minradio${minradio}"
dir_dest=${path}/graph_${name_path}
dir_dest_processed=${path}/graphs_preprocessed/graph_${name_path}
python create_graphs.py --dir ${data_path} --dir_dest ${dir_dest} --minradio ${minradio} --min_num_neighbours ${min_num_neighrbors} \
--weight_radius_w ${weight_radius_w} --weight_radius_h ${weight_radius_h} --mult_punct_w ${j_h} --mult_punct_h ${j_w} \
--max_width_line ${max_width_line} --hisclima "true" --do_spans "false" --data_path_tablelabel ""  --reading_order "false"
python preprocess.py ${dir_dest} ${dir_dest_processed}


## ROW
minradio=0.1
min_num_neighrbors=10
weight_radius_h=4
weight_radius_w=0
j_h=1
j_w=1
name_path="k${min_num_neighrbors}_wh${weight_radius_h}ww${weight_radius_w}jh${j_h}jw${j_w}_maxwidth${max_width_line}_minradio${minradio}"
dir_dest=${path}/graph_${name_path}
dir_dest_processed=${path}/graphs_preprocessed/graph_${name_path}
python create_graphs.py --dir ${data_path} --dir_dest ${dir_dest} --minradio ${minradio} --min_num_neighbours ${min_num_neighrbors} \
--weight_radius_w ${weight_radius_w} --weight_radius_h ${weight_radius_h} --mult_punct_w ${j_h} --mult_punct_h ${j_w} \
--max_width_line ${max_width_line} --hisclima "true" --do_spans "false" --data_path_tablelabel ""  --reading_order "false"
python preprocess.py ${dir_dest} ${dir_dest_processed}

echo ${name_path}

### SPANS
hisclima=true
minradio=0.3
min_num_neighrbors=10
weight_radius_w=4
weight_radius_h=0
j_h=3
j_w=3
max_width_line=0.5
name_path="k${min_num_neighrbors}_wh${weight_radius_h}ww${weight_radius_w}jh${j_h}jw${j_w}_maxwidth${max_width_line}_minradio${minradio}_span"
dir_dest=${path}/graph_${name_path}
dir_dest_processed=${path}/graphs_preprocessed/graph_${name_path}
python create_graphs.py --dir ${data_path} --dir_dest ${dir_dest} --minradio ${minradio} --min_num_neighbours ${min_num_neighrbors} \
--weight_radius_w ${weight_radius_w} --weight_radius_h ${weight_radius_h} --mult_punct_w ${j_h} --mult_punct_h ${j_w} \
--max_width_line ${max_width_line} --hisclima "true" --do_spans "true" --data_path_tablelabel ""  --reading_order "true"
python preprocess.py ${dir_dest} ${dir_dest_processed} si
echo ${name_path}
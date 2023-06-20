#!/usr/bin/env bash
loss=NLL
ngf=64,64,64,64
layers_MLP=64,64,64,64
epoch=4000
try=1
conjugate=ROW
name_data=graph_k10_wh4ww0jh1jw1_maxwidth0.5_minradio0.1
data_path=data/graphs/graphs_preprocessed
# models=( edgeconv transformer )
model=edgeconv
steps=800,2000
gamma_step=0.5
alpha_FP=5
metric=loss
mlp_do=0
do_adj=0.3
base_lr=0.01
test_lst=/data/HisClima/HisClimaProd/DLA/HisClima_0/test.lst
train_lst=/data/HisClima/HisClimaProd/DLA/HisClima_0/trainval.lst
val_lst=/data/HisClima/HisClimaProd/DLA/HisClima_0/val.lst
cd ..

mkdir -p works/works_HisClima_AlbatrossAndJeannette_NC

python main.py --batch_size 32 \
--data_path ${data_path}/${name_data}/ \
--epochs ${epoch} --seed ${try} --trans_prob 0 \
--exp_name HisClima_JeanetteAlbatross_NC_ROW \
--work_dir works/works_HisClima_AlbatrossAndJeannette_NC/${conjugate}/work \
--test_lst ${test_lst} \
--train_lst ${train_lst} \
--do_val --val_lst ${val_lst} --show_val 100 --metric ${metric} --mlp_do ${mlp_do} --do_adj ${do_adj} \
--load_model True --show_test 1000 --model ${model} --alpha_FP ${alpha_FP} --layers_MLP ${layers_MLP} \
--layers ${ngf} --adam_lr ${base_lr} --conjugate ${conjugate} --classify EDGES --g_loss ${loss} --steps ${steps} --gamma_step ${gamma_step}

conjugates=COL
name_data=graph_k10_wh0ww4jh1jw1_maxwidth0.5_minradio0.1 # COL CELL
python main.py --batch_size 32 \
--data_path ${data_path}/${name_data}/ \
--epochs ${epoch} --seed ${try} --trans_prob 0 \
--exp_name HisClima_JeanetteAlbatross_NC_COL \
--work_dir  works/works_HisClima_AlbatrossAndJeannette_NC/${conjugate}/work \
--test_lst ${test_lst} \
--train_lst ${train_lst} \
--do_val --val_lst ${val_lst} --show_val 100 --show_train 100 --metric ${metric} \
--load_model True --show_test 1000 --model ${model} --alpha_FP ${alpha_FP} --mlp_do ${mlp_do} --do_adj ${do_adj} --layers_MLP ${layers_MLP} \
--layers ${ngf} --adam_lr ${base_lr} --conjugate ${conjugate} --classify EDGES --g_loss ${loss} --steps ${steps} --gamma_step ${gamma_step}

################HEADER
epoch=2000
name_data=graph_k10_wh0ww0jh1jw1_maxwidth0.5_minradio0
python main.py --batch_size 32 \
--data_path ${data_path}/${name_data}/ \
--epochs ${epoch} --seed ${try} \
--exp_name HisClima_JeanetteAlbatross_NC_HEADER \
--work_dir  works/works_HisClima_AlbatrossAndJeannette_NC/HEADER/work \
--test_lst ${test_lst} \
--train_lst ${train_lst} \
--do_val --val_lst ${val_lst} --trans_prob 0 \
--load_model True --show_val 100 --show_train 100 --model ${model} \
--layers ${ngf} --adam_lr ${base_lr} --classify HEADER --g_loss ${loss} --gamma_step ${gamma_step}

epoch=1000
conjugate=SPAN
name_data=graph_k10_wh0ww4jh3jw3_maxwidth0.5_minradio0.3_span
alpha_FP=0.1
metrics=( loss )
do_adj=0
steps=1000,1200,1400,1800
base_lr=0.01

python main.py --batch_size 256 \
--data_path ${data_path}/${name_data}/ \
--epochs ${epoch} --seed ${try} --trans_prob 0 \
--work_dir works/works_HisClima_AlbatrossAndJeannette_NC/${conjugate}/work \
--test_lst ${test_lst} \
--train_lst ${train_lst} \
--do_val --val_lst ${val_lst} --show_val 100 --metric ${metric} --mlp_do ${mlp_do} --do_adj ${do_adj} \
--load_model True --show_test 1000 --model ${model} --alpha_FP ${alpha_FP} --layers_MLP ${layers_MLP} \
--layers ${ngf} --adam_lr ${base_lr} --conjugate ${conjugate} --classify EDGES --g_loss ${loss} --gamma_step ${gamma_step} --steps ${steps}
cd launchers

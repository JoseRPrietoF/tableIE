path_col=../works/works_HisClima_AlbatrossAndJeannette_NC/COL/work/results.txt
path_row=../works/works_HisClima_AlbatrossAndJeannette_NC/ROW/work/results.txt
path_header=../works/works_HisClima_AlbatrossAndJeannette_NC/HEADER/work/results.txt
path_span=../works/works_HisClima_AlbatrossAndJeannette_NC/SPAN/work/text_results/ids
nexp=1_span
min_w=0.5
LM_header=headers/AlbatrossAndJeannette/train/models/lm.pkl
path_hyp_coords=lines_GT_content_GT_Coords_test
use_gt=false
USE_GT_COL=${use_gt}
USE_GT_ROW=${use_gt}
USE_GT_H=${use_gt}
path_save=../works/works_HisClima_AlbatrossAndJeannette_NC/IE_hyp/
mkdir ${path_save}
# python IE
python extract_files_PAGE.py --path_hyp_coords ${path_hyp_coords} --path_header ${path_header} --path_row ${path_row} --path_col ${path_col} --path_save ${path_save} --nexp ${nexp} --min_w ${min_w} --path_span ${path_span} --USE_GT_COL ${USE_GT_COL} --USE_GT_ROW ${USE_GT_ROW} --USE_GT_H ${USE_GT_H} --LM_header ${LM_header}
# metrica
# exp_name=NER_exp${nexp}_GT
exp_name=NER_exp${nexp}
path_IE_GT=GT_IE_test.txt
path_hyp_file=${path_save}${exp_name}
/data/HisClima/HisClimaProd/IE/evaluateIE.o ${path_hyp_file}/hyp_file.txt ${path_IE_GT}
mv FN.txt ${path_hyp_file}/FN.txt
mv FP.txt ${path_hyp_file}/FP.txt
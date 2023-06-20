path_results=../works/works_HisClima_AlbatrossAndJeannette_NC/SPAN/work/results.txt
path_coords=lines_GT_content_GT_Coords_test
files_to_use=/data/HisClima/HisClimaProd/DLA/HisClima_0/test.lst
use_gt=false
path_save=../works/works_HisClima_AlbatrossAndJeannette_NC/SPAN/work/text_results
python extraction_span_PAGE.py --span_results ${path_results} --path_save ${path_save} --path_coords ${path_coords} --files_to_use ${files_to_use} --use_gt ${use_gt} --min_w 0.5

import os, sys, glob, numpy as np, shutil
from networkx.algorithms.shortest_paths.unweighted import all_pairs_shortest_path
import networkx as nx
from numpy.lib.function_base import append
import dill as pickle 
from math import inf
from nltk.lm.preprocessing import padded_everygram_pipeline, pad_both_ends
from nltk.util import everygrams
import torch_geometric

replace_points = True # False in DAS. True otherwise
USE_GT_COL = False
USE_GT_ROW = False
USE_GT_H = False
CONJUGATE = False
MIN_w = 0.95
import argparse

def preprocess(s:str):
    return s.replace("!print", "").replace("!manuscript", "")

def create_dir(path:str):
    if not os.path.exists(path):
        os.mkdir(path)

def read_results(fname, conjugate=True):
    """
    Since the differents methods tried save results in different formats,
    we try to load all possible formats.
    """
    results = {}
    if conjugate:
        if type(fname) == str: 
            f = open(fname, "r")
            lines = f.readlines()
            f.close()
            for line in lines[1:]:
                id_line, label, prediction = line.split(" ")
                id_line = id_line.split("/")[-1].split(".")[0]
                results[id_line] = (int(label), np.exp(float(prediction.rstrip())) )
        else:
            for id_line, label, prediction in fname:
                id_line = id_line.split("/")[-1].split(".")[0]
                results[id_line] = int(label), np.exp(float(prediction))
    else:
        if type(fname) == str: 
            f = open(fname, "r")
            lines = f.readlines()
            f.close()
            for line in lines[1:]:
                *id_line, label, prediction = line.split(" ")
                id_line = " ".join(id_line)
                results[id_line] = int(label), np.exp(float(prediction))
        else:
            for fname, label, prediction, (i,j) in fname:
                id_line = fname
                results[id_line] = int(label), np.exp(float(prediction))
    return results

def extract_fnames(results):
    fnames = set()
    for c in results.keys():
        name = c.split(" ")[0]
        fnames.add(name)
    return fnames

def load_graph(file_results, USE_GT):
    print(file_results)
    results = read_results(file_results, conjugate=CONJUGATE)
    names_files = extract_fnames(results)
    res = {}
    hyps, gts = [], []
    for name_file in names_files:
        G = nx.Graph()
        cont = 0
        for c in results.keys():
            cont +=1 
            # print(cont)
            if name_file in c:
                fname, origen, destino = c.split(" ")
                origen = f'{name_file} {origen}'
                
                destino = f'{name_file} {destino}'
                gt, hyp = results[c]
                hyps.append(hyp > MIN_w)
                gts.append(gt)
                # print(f'{origen} {destino} {gt} {hyp}')
                if USE_GT:
                    is_link = gt
                else:
                    # print(hyp, MIN_w, hyp > MIN_w)
                    is_link = hyp > MIN_w
                if is_link:
                    G.add_edge(origen, destino)
                    G.add_edge(destino, origen)
        cc = nx.algorithms.community.label_propagation.asyn_lpa_communities(G, seed=0)
        cc = [list(c) for c in cc]
        res[name_file] = cc
    hyps = np.array(hyps)
    gts = np.array(gts)
    corrects = hyps == gts
    acc = corrects.sum() / len(corrects)
    print(f"Acc: {acc}")
    return res, results
    
def load_headers(path_header, USE_GT):
    fheader = open(path_header, "r")
    lines = fheader.readlines()
    fheader.close()
    res = {}
    gts, hyps = [], []
    for line in lines[1:]:
        line = line.strip()
        *lId, header_gt, header_hyp = line.split(" ")
        lId = " ".join(lId)
        header_hyp = np.exp(float(header_hyp))
        header_gt = float(header_gt)
        id_line = lId.split("/")[-1]  # Cuidado
        gts.append(header_gt)
        hyps.append(header_hyp > MIN_w)
        if USE_GT:
            is_h = header_gt
        else:
            is_h = header_hyp > MIN_w
        res[id_line] = is_h
    hyps = np.array(hyps)
    gts = np.array(gts)
    corrects = hyps == gts
    acc = corrects.sum() / len(corrects)
    print(f"Acc: {acc}")
    return res

def cut(fname, cc_col, res_rows, USE_GT):
    def all_vs_all(cc_col):
        res = []
        for r in cc_col:
            for r2 in cc_col:
                r = r.split(fname)[-1].strip()
                r2 = r2.split(fname)[-1].strip()
                res.append((f'{fname} {r} {r2}', (r,r2)))
        return res
    

    G = nx.Graph()
    G.add_nodes_from(cc_col)
    all_posible_edges_row = all_vs_all(cc_col)
    total = 0
    for posible_link, (r,r2) in all_posible_edges_row:
        gt, hyp = res_rows.get(posible_link, (0, 0))
        if USE_GT:
            is_link = gt
        else:
            is_link = hyp > MIN_w
        total += is_link
        if is_link:
            # TODO revisar
            r = f'{fname} {r}'
            r2 = f'{fname} {r2}'
            G.add_edge(r, r2)
    cc = nx.algorithms.community.label_propagation.asyn_lpa_communities(G)
    cc = [list(c) for c in cc]
    return cc

def set_header(cc_res, res_headers, fname):
    res = []
    
    # print(cc_res)
    for components in cc_res:
        # print(components)
        count_headers = 0
        for component in components:
            is_header = res_headers.get(component, None)# si el fichero se ha creado con lineas de hyp con mi RPN
            if is_header is None:
                raise Exception(f'{component} not found in headers')
            count_headers += is_header
        if count_headers/len(components) >= 0.5:
            is_header = True
        else:
            is_header = False
        res.append([components, is_header])
    return res

def read_hyp_coords_file(path:str):
    f = open(path, "r")
    lines = f.readlines()
    f.close()
    res = {}
    for line in lines:
        # if "Albatross_vol009of055-050-0_194" in line:
        #     print(line)
        line = line.strip()
        
        l, coords = line.split("Coords:")
        coords = coords.replace("( ", "").replace(" )", "").strip()
        coords = [[int(x.split(",")[0]), int(x.split(",")[1])] for x in coords.split(" ")]
        lId, *text = l.split(" ")
        text = " ".join(text)
        text = text.strip()
        if replace_points:
            if text.endswith("."):
                text = text[:-1]
        text = text.replace("<decimal>", ".")
        page_name, lId = lId.split(".")
        lId = f'{page_name} {lId}'
        # if "line_1583317643037_9931" in lId:
        #     print(coords, text, page_name, lId)
        if res.get(lId) is not None:
            print(lId)
            raise Exception("IDs repetidas!!")
        res[lId] = [coords, text]
    return res

def search_col(words_header, headers):

    for query_word, fname_query in words_header:
        query_word = query_word.upper()
        for header in headers:
            if replace_points:
                header = header.replace(".", "").replace(",", "")
            if "HOUR" not in header:
                for h in header.split(" "):
                    if h == query_word:
                        return query_word, fname_query

    # print("NOT FOUND for -------------------> ", headers)
    return None, None

def search_header_span(fname, ids_span_headers, headers, headers_ids, file_text):

    query_word, fname_query = "", ""
    for h in headers:
        query_word += f'{h} '
        fname_query += f'{h}_'
    return query_word, fname_query

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def print_file(cc, path_save, fname, file_text, hours_col_ordered, cc_rows, ids_span_headers=None, LM_headers=None):
    
    def get_cc_line(cc, line):
        for group in cc:
            if line in group:
                return group
    
    def search_hour(cc_row_cell, ):
        if hours_col_ordered is not None:
            for line in cc_row_cell:
                for i, (coords, idLine, text_hour) in enumerate(hours_col_ordered):
                    if line == idLine:
                        if has_numbers(text_hour):
                            if "." in text_hour:
                                continue
                        return str(text_hour), idLine
        best_coord = 99999
        info_best_cell = None
        for line in cc_row_cell:
            coords, text_hour = file_text.get(line)
            x_min = np.min([x[0] for x in coords])
            if best_coord > x_min:
                if "NOON" in text_hour or "MID" in text_hour or has_numbers(text_hour):
                    if has_numbers(text_hour):
                        if "." in text_hour:
                            continue
                    best_coord = x_min
                    info_best_cell = (str(text_hour), line)
        if info_best_cell is not None:
            return info_best_cell[0], info_best_cell[1]
        # print("None search hour")
        return None, None
    cc_res = []
    res_strings = []
    for lines_cc, isheader in cc:
        cc_aux = []
        
        for line_cc in lines_cc: 
            # lId = line_cc.split("line")[-1]
            lId = line_cc
           
            name_line = lId
            coords, text = file_text.get(name_line, (None, None))
            if text is None:
                name_line = f'{fname} {lId}' # lines HYP
                coords, text = file_text.get(name_line, (None, None))
                if text is None:
                    # text = ([], "")
                    # print(f'No text for line {name_line} (print_file)')
                    continue
            cc_aux.append([coords, text, lId])
        cc_aux.sort(key=lambda x: x[0][0][1]) #ordenamos líneas segun el RO que indique la coordenada Y superior irzquierda
        if cc_aux:
            cc_res.append([cc_aux, isheader])
    cc = cc_res
    cc.sort(key=lambda x: x[0][0][0][0][1])

    headers = []
    headers_ids = []
    headers_coords = []
    for cc_row, is_header in cc:
        if is_header:
            # coords, text, lId = cc_row[0]
            for coords, text, lId in cc_row:
                headers.append(text)
                headers_ids.append(lId)
                headers_coords.append([coords, text, lId])
    if not headers:
        # print("No header for ", cc)
        return

    if ids_span_headers is not None:
        query_word, fname_query = search_header_span(fname, ids_span_headers, headers, headers_ids, file_text)
    else:
        # query_word, fname_query = search_col(words_header, headers)
        raise Exception(f"ids_span_headers is None")
    if query_word is None:
        # print("->> ", fname, headers)
        return

    path_col = os.path.join(path_save, f'{fname_query}_{fname}.txt')
    headers_coords.sort(key=lambda x: x[0][0][1])
    headers_String = [x[1] for x in headers_coords]
    headers_String = " ".join(headers_String)
    f = open(path_col, "w")
    f.write(f'{headers_String}\n')
    # print(headers_String)
    last_text = ""
    query_word_ = query_word.strip()
    query_word = get_header_from_LM(query_word_, LM_headers)
    # print(f' -----------> {query_word_}  =>  {query_word}')
    for j, (cc_row, is_header) in enumerate(cc):
        if is_header:
            continue
        cell_String = [x[1] for x in cc_row]
        cell_String = " ".join(cell_String)
        #Lista de celda ya ordenada
        # Ahora buscar su hora correspondiente a partir de las variables hours_col_ordered y cc_rows
        
        lId  = f'{cc_row[0][-1]}'
        cc_row_cell = get_cc_line(cc_rows, lId)
        if cc_row_cell is None:
            lId  = f'{cc_row[0][-1]}' #hyp textlines
            cc_row_cell = get_cc_line(cc_rows, lId)
            if cc_row_cell is None: 
                # print(f'Not found cc for {lId} in rows for file {fname}')
                return

        ## Buscar ahora cual de las celdas esta en la lista de horas
        text_hour, idLine = search_hour(cc_row_cell)
        if text_hour is None:
            # print(f'Not found hours for {cc_row_cell} in {fname}')
            return
        pre = "" #AM or PM
        num_table = 0
        if cc_row[0][0][0][1] > 2000: # PM
            pre = "P. M."
            num_table = 1
        else:
            pre = "A. M."

        #resolver problema comillas
        if cell_String == "\"" or cell_String.find("\"") != -1:
            if last_text == "" or last_text == " ": # comillas vacias, suele ser error de deteccion de lineas
                cell_String = ""
            else:
                cell_String = f'{cell_String} [{last_text}]'
        else:
            last_text = cell_String 
        f.write(f'{pre} {text_hour} {cell_String}\n')
        cell_String = preprocess(cell_String)
        text_hour = preprocess(text_hour)
        try:
            text_hour_int = int(text_hour)
        except:
            text_hour_int = 1
        if cell_String and ((text_hour_int >= 1 and text_hour_int < 20) or ("MID" in text_hour or "NOON" in text_hour)):
            string_res = f'{fname} 1.0 {query_word}|table{num_table}_{text_hour} {cell_String}'
            res_strings.append(string_res)
    f.close()
    return res_strings

def load_LM(p:str):
    with open(p, "rb") as fout:
        res_dict = pickle.load(fout)
    return res_dict

def get_header_from_LM(query_word:str, lm_dict:dict):
    """
    lm_likelihood = sum([lm.logscore(ngram[-1], ngram[:-1]) for ngram in bgr])
    lm_prior = log(priors[key2],2)
    actualProb = lm_likelihood + lm_prior
    """
    query_word = preprocess(query_word)
    bestScore = -inf
    bestKey = None
    priors = lm_dict.get("priors")
    n_gram = lm_dict.get("ngram")
    padded_sent = pad_both_ends(list(query_word), n_gram)
    padded_sent = list(padded_sent)
    lms = lm_dict.get("lm_dict")
    classes_dict_inv = lm_dict.get("classes_dict_inv")
    for key2, lm in lms.items():
        bgr = list(everygrams(padded_sent, max_len = n_gram))
        logscore = sum([lm.logscore(ngram[-1], ngram[:-1]) for ngram in bgr])
        if priors is not None:
            priors_key = priors[key2]
            logscore += np.log(priors_key)
        if (logscore > bestScore):
            bestScore = logscore
            bestKey = key2
    if bestKey is None:
        raise Exception(f'Not found key for query word {query_word} ({len(lm_dict)} LMs)')
    header = classes_dict_inv.get(bestKey)
    if header is None:
        raise Exception(f'Not found header {header} in dict classes {classes_dict_inv}')
    return header

def get_hours(cc_cols, file_text, fname):
    def search():
        for cc_col in cc_cols:
            for line_cc in cc_col:
                name_line = line_cc
                text = file_text.get(name_line)
                if text is None:
                    # print(f'    **** {name_line} text not found')
                    continue
                else:
                    coords, text = text
                    text = text.upper()
                    if "HOUR" in text:
                        return cc_col
        return None
    

    cc_hours = search()
    if cc_hours is None:
        return None
    res = []
    for component in cc_hours:
        name_line = component
        text = file_text.get(name_line)
        if text is None:
            text = ([], "")
            # print(f'No text for line {name_line} (get_hours)')
            continue
        coords, text = text
        text = text
        res.append([coords, component, text])
    res.sort(key=lambda x: x[0][0][1])
    return res

def is_hour_col(cc_cols, file_text, fname):
    for line_cc in cc_cols:

        name_line = line_cc
        text = file_text.get(name_line)
        if text is None:

            text = ([], "")
            # print(f'No text for line {name_line} (is_hour_col)')
            continue
            # raise Exception(f'No text for line {name_line}')
        coords, text = text
        text = text.upper()
        if "HOUR" in text:
            return True
    return False

def read_ids_span(file_p:str):
    f = open(file_p, "r")
    lines = f.readlines()
    ls = []
    for line in lines:
        aux = []
        for x in line.strip().split("\t"):
            aux.append(x)
        ls.append(aux)
    f.close()
    return ls

def main(args):
    nexp = args.nexp
    USE_GT_COL = args.USE_GT_COL
    USE_GT_ROW = args.USE_GT_ROW
    USE_GT_H = args.USE_GT_H
    # n_gram = args.n_gram

    path_save = args.path_save
    path_col = args.path_col
    path_row = args.path_row
    path_header = args.path_header
    path_hyp_coords = args.path_hyp_coords
    LM_headers = load_LM(args.LM_header)
    path_save = os.path.join(path_save, f'NER_exp{nexp}')
    if USE_GT_ROW or USE_GT_COL or USE_GT_H:
        path_save += "_GT"
    create_dir(path_save)
    
    """Info exp"""
    info_path = os.path.join(path_save, "info_exp")
    f = open(info_path, "w")
    f.write(f'path_hyp_text {path_hyp_coords} \n')
    f.write(f'path_col {path_col} \n')
    f.write(f'path_row {path_row} \n')
    f.write(f'path_header {path_header} \n')
    if args.path_span:
        f.write(f'path_span {args.path_span} \n')
    f.close()
    # USE_GT_COL = False
    # USE_GT_ROW = False
    # USE_GT_H = False
    cc_cols, cols_results = load_graph(path_col, USE_GT_COL)
    cc_rows, rows_results = load_graph(path_row, USE_GT_ROW)
    # exit()
    # USE_GT_H = True
    headers = load_headers(path_header, USE_GT_H)
    # exit()
    file_text = read_hyp_coords_file(path_hyp_coords)
    # print(file_text.keys)
    path_save2 = os.path.join(path_save, "output")
    create_dir(path_save2)
    all_strings = []
    for fname, ccs in cc_cols.items():
        # print(f'File {fname}')

        if args.path_span:
            path_span_file = os.path.join(args.path_span, fname)
            ids_span_headers = read_ids_span(path_span_file)
        else:
            ids_span_headers = None
        hours_col_ordered = get_hours(ccs, file_text, fname)
        for count_c, cc in enumerate(ccs):
            # Is hour? -> skip
            if is_hour_col(cc, file_text, fname):
                continue
            cc_rows_cut = cut(fname, cc, rows_results, USE_GT_ROW)
            cc_rows_headers = set_header(cc_rows_cut, headers, fname)
            res_strings = print_file(cc_rows_headers, path_save2, fname, file_text, hours_col_ordered, cc_rows.get(fname), ids_span_headers, LM_headers)
            if res_strings is not None:
                all_strings.extend(res_strings)
            # else:
            #     print(f"res_strings is NONE {count_c}")
    path_save = os.path.join(path_save, "hyp_file.txt")
    f = open(path_save, "w")
    print(f"Saving  ==  {path_save}")
    all_strings = list(set(all_strings))
    for line in all_strings:
        f.write(f'{line}\n')
    f.close()
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create the spans')
    parser.add_argument('--path_save', type=str, help='path to save the save')
    parser.add_argument('--path_hyp_coords', type=str, help='The span results file')
    parser.add_argument('--path_span', type=str, help='The span results file')
    parser.add_argument('--path_col', type=str, help='The span results file')
    parser.add_argument('--path_row', type=str, help='The span results file')
    parser.add_argument('--path_header', type=str, help='The span results file')
    parser.add_argument('--min_w', type=float, default=0.95, help='The span results file. If its empty the GT will be used')
    parser.add_argument('--nexp', type=str, default=1, help='The span results file. If its empty the GT will be used')
    parser.add_argument('--USE_GT_COL', type=str, default="false", help='The span results file')
    parser.add_argument('--USE_GT_ROW', type=str, default="false", help='The span results file')
    parser.add_argument('--USE_GT_H', type=str, default="false", help='The span results file')
    parser.add_argument('--CONJUGATE', type=str, default="false", help='The span results file')
    parser.add_argument('--LM_header', type=str, default="false", help='The span results file')
    # parser.add_argument('--n_gram', type=int, default=2, help='The span results file')
    args = parser.parse_args()
    create_dir(args.path_save)
    args.CONJUGATE = args.CONJUGATE.lower() in ["si", "true", "yes"]
    args.USE_GT_COL = args.USE_GT_COL.lower() in ["si", "true", "yes"]
    args.USE_GT_ROW = args.USE_GT_ROW.lower() in ["si", "true", "yes"]
    args.USE_GT_H = args.USE_GT_H.lower() in ["si", "true", "yes"]
    main(args)
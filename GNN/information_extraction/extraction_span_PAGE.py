from extract_files_PAGE import read_results, read_hyp_coords_file, extract_fnames
import argparse
import networkx as nx
import os

def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_lines(fpath):
    f = open(fpath, "r")
    lines = f.readlines()
    f.close()
    lines = [x.strip().split(".")[0] for x in lines]
    return lines

def load_graph(file_results, USE_GT, args):
    
    results = read_results(file_results, conjugate=args.conjugate == "true")
    names_files = extract_fnames(results)
    res = {}
    for name_file in names_files:
        # if "Albatross_vol009of055-050-0" not in name_file:
        #     continue
        G = nx.DiGraph()
        for c in results.keys():
            if name_file in c:
                fname, origen, destino = c.split(" ")
                
                origen = f'{name_file} {origen}'
                
                destino = f'{name_file} {destino}'
                # G.add_node(origen)
                # G.add_node(destino)
                gt, hyp = results[c]
                # print(f'{origen} {destino} {gt} {hyp}')
                if USE_GT:
                    is_link = gt
                else:
                    # print(hyp, MIN_w, hyp > MIN_w)
                    is_link = hyp > args.min_w
                # print(is_link, hyp)
                # if (origen.startswith(f"{fname} {fname}") or destino.startswith(f"{fname} {fname}")) and is_link:
                #     print(origen, destino, is_link)
                if is_link:
                    G.add_edge(origen, destino)
                    # G.add_edge(destino, origen)
        res[name_file] = G
    # exit()
    return res, results

def main(args):
    files_to_use = read_lines(args.files_to_use)
    print(files_to_use)
    graphs_files, span_results = load_graph(args.span_results, args.use_gt != "false", args)
    file_text = read_hyp_coords_file(args.path_coords)
    # print("Albatross_vol009of055-050-0_194" in file_text)
    # print("Albatross_vol009of055-050-0.xml-Albatross_vol009of055-050-0_194" in file_text)
    # print(file_text.keys())
    dir_save_text = os.path.join(args.path_save, "text")
    dir_save_ids = os.path.join(args.path_save, "ids")
    create_dir(dir_save_ids)
    create_dir(dir_save_text)
    print(f'Saving on \n {dir_save_text} \n {dir_save_ids}')
    # exit()
    for raw_path in files_to_use:
        
        # if "Albatross_vol009of055-050-0" not in raw_path:
        #     continue
        print(f'################## {raw_path} ###############')
        querys = []
        querys_str = []
        file_name_p = raw_path.split("/")[-1].split(".")[0]
        path_save_file_text = os.path.join(dir_save_text, file_name_p)
        path_save_file_ids = os.path.join(dir_save_ids, file_name_p)
        ffile_text = open(path_save_file_text, "w")
        ffile_ids = open(path_save_file_ids, "w")
        if files_to_use is not None and file_name_p not in files_to_use:
            continue
        G_file = graphs_files.get(file_name_p, None)
        if G_file is None:
            print(f'{file_name_p} not used')
            continue
        # print(G_file, G_file.is_directed())
        # leafs = set([f for f in G_file.nodes if nx.DiGraph.successors(G_file, f) ])
        sources = set([g[0] for g in G_file.edges])
        leafs = set([f for f in G_file.nodes if f not in sources ])

        # print(len(leafs), len(G_file.nodes))
        # exit()
        for n in list(G_file.nodes):
            
            ancestors = nx.algorithms.dag.ancestors(G_file, source=n)
            # print(ancestors, leafs)
            if not ancestors:
                # path = list(nx.dfs_tree(G_file, source=n, depth_limit=10).edges())
                for leaf in leafs:
                    coords, text = file_text.get(leaf)
                    print("\n\nleaf", leaf, "||", text)
                    print("raw_path", raw_path)
                   
                    # leaf Albatross_vol009of055-050-0_156
                    # leaf vol003_206_0line_1579108173444_45124
                    # -> "Albatross_vol009of055-050-0.xml-Albatross_vol009of055-050-0_194"
                    path = list(nx.algorithms.simple_paths.all_simple_paths(G_file, n, leaf))
                    if not path:
                        continue
                    path = path[0]
                    q = ""
                    for p in path:
                        # print("P", p)
                        str_filetext = p.replace("line", ".xml-line") #vol003_064_0.xml-line_1582119345200_5882'
                        str_filetext = p
                        try:
                            # print("str_filetext", str_filetext)
                            coords, text = file_text.get(str_filetext)
                        except Exception as e:
                            # print("n -> ", n)
                            # print(p, " ------- ", str_filetext)
                            # print(list(file_text.keys())[:5])
                            # raise e
                            text = ""

                        q += f'{text} '
                    
                    querys_str.append(q)
                    path_str = "\t".join(ps for ps in path)
                    print("path", path, q)
                    ffile_ids.write(f'{path_str}\n')
                    ffile_text.write(f'{q}\n')
        ffile_text.close()
        ffile_ids.close()

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create the spans')
    parser.add_argument('--path_save', type=str, help='path to save the save')
    parser.add_argument('--span_results', type=str, help='The span results file. ')
    parser.add_argument('--path_coords', type=str, help='The span results file')
    parser.add_argument('--conjugate', type=str, default="false", help='The span results file. If its empty the GT will be used')
    parser.add_argument('--files_to_use', type=str, default="", help='The span results file. If its empty the GT will be used')
    parser.add_argument('--min_w', type=float, default=0.95, help='The span results file. If its empty the GT will be used')
    parser.add_argument('--use_gt', type=str, default="false", help='The span results file. If its empty the GT will be used')
    
    args = parser.parse_args()
    create_dir(args.path_save)
    main(args)

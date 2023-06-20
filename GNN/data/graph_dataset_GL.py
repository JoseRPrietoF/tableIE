import os.path as osp
import os, re, time
import glob, pickle
import torch
from torch_geometric.data import Dataset, Data, DataLoader
import numpy as np
try:
    from utils.optparse_graph import Arguments as arguments
except:
    import sys
    sys.path.append('../utils')
    from optparse_graph import Arguments as arguments
# from torch_geometric.utils import grid
# import spacy
import logging

def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        print('{:s} function took {:.3f} ms'.format(f.__name__, (time2-time1)*1000.0))

        return ret
    return wrap

class Dataset_GL(Dataset):
    """
    In order to create a torch_geometric.data.InMemoryDataset, you need to implement four fundamental methods:

    torch_geometric.data.InMemoryDataset.raw_file_names():
    A list of files in the raw_dir which needs to be found in order to skip the download.

    torch_geometric.data.InMemoryDataset.processed_file_names():
    A list of files in the processed_dir which needs to be found in order to skip the processing.

    torch_geometric.data.InMemoryDataset.download():
    Downloads raw data into raw_dir.

    torch_geometric.data.InMemoryDataset.process():
    Processes raw data and saves it into the processed_dir.
    """
    def __init__(self, root, split, flist, opts=None, transform=None, pre_transform=None):
        # super(ABPDataset_Header, self).__init__(root, transform, pre_transform, None)
        self.root = None
        self.transform = transform
        self.pre_transform = pre_transform
        self.pre_filter = None
        self.__indices__ = None

        self.opts = opts
        self.processed_dir_ = os.path.join(opts.work_dir, split)
        if not os.path.exists(self.processed_dir_):
            os.mkdir(self.processed_dir_)
        self.pre_transform = pre_transform
        self.flist = flist
        self.flist_processed = []
        # self.processed_dir = self.pathself.text_info = opts.text_info
        self.text_length = opts.text_length
        self.img_feats = opts.img_feats
        self.transform = transform

        # if opts.fasttext:
        #     self.model = ft.load_fasttext_format("/data2/jose/word_embedding/fastext/german/cc.de.300.bin")

        self.dict_clases = {
            'CH': 0,
            'O': 1,
            'D': 1,
        }
        self.num_classes = 2

        self.ids = []
        self.ids_labels = []
        self.labels = []

        # POS Tagging etc from SPACY


        self.preprocessed = not self.opts.not_preprocessed
        # if opts.fix_class_imbalance:
        #     self.class_weights = self.get_prob_class()
        #     self.prob_class = self.class_weights

        # if self.text_info and not self.preprocessed:
        #     self.nlp = spacy.load('de')

    def get_prob_class(self):
        counts = list(zip(*np.unique(self.A,return_counts=True)))
        total = len(self.A)
        self.prob_class = [i[1]/total for i in counts]
        self.weights = [total/i[1] for i in counts]
        return self.weights

    @property
    def raw_file_names(self):
        # return self.flist
        return []
    @property
    def processed_file_names(self):
        # return self.flist
        return []

    def __len__(self):
        """
        Returns the number of examples in your dataset.
        :return:
        """
        # print(self.processed_file_names)
        return len(self.flist)

    def download(self):
        # Download to `self.raw_dir`.
        # self.raw_paths = []
        print("Download?")

    # def get_edge_info(self, edges):
    #     edge_index, info_edges = [], []
    #     for (i,j), info in edges:
    #         edge_index.append((i,j))
    #         info_edges.append(info)
    #     return np.array(edge_index).T, info_edges

    def get_positions(self, nodes):
        res = []
        for node in nodes:
            res.append(node[:2])
        return res

    def get_nodes(self, nodes):
        """Not used if its preprocessed"""

        if self.text_length and self.text_info and self.img_feats:
            return nodes

        res = []
        POS_len = len(list(self.POS_tag))
        ent_type_len = len(list(self.ent_type))
        text_len = POS_len + ent_type_len
        img_len = 300*50*3
        for node in nodes:

            len_n = len(node)
            hasta = len_n - (text_len + 1 + img_len)

            n = node[:hasta]
            text_feats = node[hasta:hasta+text_len]
            len_text = node[hasta+text_len:hasta+text_len+1]
            img = node[hasta+text_len+1:]

            if self.text_length:
                n.extend(len_text)
            if self.text_info:
                n.extend(text_feats)
            # if self.fasttext:
            #
            #     try:
            #         res_ft = self.model.wv[w][0]
            #     except:
            #         res_ft = np.zeros((300))
                # self.model =
            elif self.img_feats:
                n.extend(img)

            res.append(n)
        return res



    def get_neighbors_feats(self, nodes):
        res = []
        for node in nodes:
            n = node[:-1]
            res.append(n)
        return res

    def process(self):
        self._process()

    def _process(self):
        i = 0
        # if not os.path.exists(osp.join(self.root, 'processed')):
        #     os.mkdir(osp.join(self.root, 'processed'))
        self.A = []
        for raw_path in self.flist:
            # Read data from `raw_path`.
            f = open(raw_path, "rb")
            data_load = pickle.load(f)
            f.close()
            ids = data_load['ids']
            nodes = data_load['nodes']
            self.ids.extend(ids)
            labels = []
            # print("Len nodes ", len(nodes))
            for label in data_load['labels']:
                try:
                    l = self.dict_clases[label['DU_header']]
                except:
                    l = label
                labels.append(l)
            A = []

            #     exit()
            for i_n, label_i in enumerate(data_load['labels']):
                # if i_n != 3:
                #     continue
                # print(label_i)
                # print(i_n, label_i)
                row_i, col_i = label_i['row'], label_i['col']
                A_i = []
                for j_n, label_j in enumerate(data_load['labels']):
                    row_j, col_j = label_j['row'], label_j['col']
                    A_i.append(col_i == col_j)
                    A.append(col_i == col_j)
                    fname = raw_path.split("/")[-1].split(".")[0]
                    self.ids_labels.append("{}_edge{}-{}".format(fname, i_n, j_n))
                #     if A_i[-1]:
                #         print("{} - node {} (col {})  to node {} (col {})  -> {}  ".format(raw_path, i_n, col_i, j_n, col_j, A_i[-1]))
                # print("{} edges".format(np.sum(A_i)))
                # exit()
            # print("len nodes ^2 ", len(nodes)**2, " len A ", len(A))
            # print(np.unique(labels, return_counts=True))
            # edge_index = torch.tensor(np.array(data_load['edges']).T, dtype=torch.long)
            # edge_index, info_edges = self.get_edge_info(data_load['edges'])
            edge_index = np.array(data_load['edges']).T
            info_edges = data_load['edge_features']
            # info_edges = np.zeros_like(data_load['edge_features'])
            # print("raw_path {} nodes {}".format(raw_path, len(nodes)))
            if not self.preprocessed:
                nodes = self.get_nodes(nodes)
            # info_edges = self.get_neighbors_feats(info_edges)
            positions = self.get_positions(nodes)
            self.labels.extend(labels)
            if len(nodes) != len(labels):
                print("Problem with nodes and labels")
                exit()
            if len(edge_index) > 0 and edge_index.shape[1] != len(info_edges):
                print(edge_index.shape[1])
                print(edge_index[:5])
                print(len(info_edges))
                print(info_edges[:5])
                print("Problem with edges")
                exit()
            # nodes_aux = nodes
            # nodes = []
            # for node in nodes_aux:
            #     nodes.append(node[-300:])
                # print(len(nodes[0]))
                # exit()
            # nodes = np.array(nodes)[:,1:2] # ONLY Y
            # nodes = np.ones_like(nodes)
            # info_edges = np.ones_like(info_edges) # NO EDGE FEATURES!
            # print(nodes.shape)
            # exit()

            self.A.extend(A)

            x = torch.tensor(nodes, dtype=torch.float)
            labels_tensor = torch.tensor(labels, dtype=torch.long)
            edge_index = torch.tensor(edge_index, dtype=torch.long)
            info_edges = torch.tensor(info_edges, dtype=torch.float)
            positions = torch.tensor(positions, dtype=torch.float)
            A = torch.tensor(A, dtype=torch.long)
            data = Data(x=x,
                        edge_index=edge_index,
                        y=labels_tensor,
                        edge_attr=info_edges,
                        pos=positions,
                        A=A,
                        )


            if self.pre_filter is not None and not self.pre_filter(data):
                continue

            if self.pre_transform is not None:
                data = self.pre_transform(data)

            torch.save(data, os.path.join(self.processed_dir_, 'data_{}.pt'.format(i)))
            self.flist_processed.append(os.path.join(self.processed_dir_, 'data_{}.pt'.format(i)))
            i += 1

    def get(self, idx):
        """Implements the logic to load a single graph.
        Internally, torch_geometric.data.Dataset.__getitem__() gets data objects
        from torch_geometric.data.Dataset.get() and optionally transforms them according to transform.
        """
        data_save = torch.load(osp.join(self.processed_dir_, 'data_{}.pt'.format(idx)))
        if self.transform:
            data_save = self.transform(data_save)
        return data_save


def get_all(path, ext="pkl"):
    if path[-1] != "/":
        path = path+"/"
    file_names = glob.glob("{}*.{}".format(path,ext))
    return file_names

if __name__ == "__main__":
    def prepare():
        """
        Logging and arguments
        :return:
        """

        # Logger
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        # --- keep this logger at DEBUG level, until aguments are processed
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # --- Get Input Arguments
        in_args = arguments(logger)
        opts = in_args.parse()


        fh = logging.FileHandler(opts.log_file, mode="a")
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        # --- restore ch logger to INFO
        ch.setLevel(logging.INFO)

        return logger, opts

    logger, opts = prepare()
    opts.tr_data = "/data/READ_ABP_TABLE/dataset111/graphs_preprocesseds/graphs_structure_PI_lenText_0.05/"
    opts.fix_class_imbalance = True
    dataset_tr = ABPDataset_Header(root=opts.tr_data, split="dev", flist=get_all(opts.tr_data), transform=None, opts=opts)
    logger.info(dataset_tr.class_weights)

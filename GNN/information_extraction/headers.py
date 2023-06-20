from nltk.lm import Laplace, KneserNeyInterpolated, WittenBellInterpolated, MLE
from nltk.lm.preprocessing import padded_everygram_pipeline, pad_both_ends
from nltk.classify import NaiveBayesClassifier
from nltk.util import everygrams
from nltk import ngrams
from math import inf
import nltk
import random
import dill as pickle 

N_GRAM = 2
NUM_NOISE = 5
TRAIN_SIZE = 1

def read_file(path:str):
    f = open(path, "r")
    # lines = f.read().splitlines()
    lines = [x.strip() for x in f.read().splitlines()]
    f.close()
    return lines

def train_test_split(lines:list,train_size:float):
    random.shuffle(lines)
    num_tr = int(len(lines)*train_size)
    lines_tr  = lines[:num_tr]
    lines_te = lines[num_tr:]
    return lines_tr,lines_te

def get_class_dic(lines:list):
    res = {}
    lastCategory = ""
    cont = -1
    dict_c_to_header = {}
    for line in lines:
        if lastCategory == "":
            lastCategory = line
            cont += 1
            dict_c_to_header[cont] = line
        else:
            if line == "#":
                lastCategory = ""
            else:
                # res[line] = lastCategory
                res[line] = cont
    return res, dict_c_to_header

def categorize_lines(lines:list, classes_dict:dict):
    lines_dict_count = {}
    lines_dict = {}
    total = 0
    for line in lines:
        key = classes_dict.setdefault(line, None)
        if key is not None:
            lines_dict.setdefault(key, []).append(list(line))
            # print(line, key)
            c = lines_dict_count.get(key, 0)
            c += 1
            lines_dict_count[key] = c
            total += 1
    return lines_dict, lines_dict_count, total

def ngram_feats(words:str, n:int):
    ngram_vocab = everygrams(words, max_len=n)
    my_dict = dict([(ng, True) for ng in ngram_vocab])
    return my_dict

def get_NB_data(lines_dict:dict):
    data = []
    for c,lines in lines_dict.items():
        for line in lines:
            feats = ngram_feats(line, n=N_GRAM)
            data.append((feats, c))
    return data

def make_noise_str(line:str, num_noise:int):
    for _ in range(num_noise):
        if len(line) > 2:
            r = random.random()
            l = random.randint(0, len(line) - 1)
            if 0 <= r <= 0.5:
                line = list(line)
                l2 = random.randint(0, len(line)-1)
                cp_line = line
                cp_line[l] = line[l2]
                cp_line[l2] = line[l]
                line = ''.join(cp_line)
            else:
                line = line[0 : l : ] + line[l + 1 : :]
    return line

def train_lm(lines_dict:dict, n:int):
    res = {}
    for key, lines in lines_dict.items():
        train_data, padded_sents = padded_everygram_pipeline(n, lines)
        model = Laplace(n) 
        # model = KneserNeyInterpolated(n)
        model.fit(train_data, padded_sents)
        res[key] = model
    return res

def evaluate_lm(lm_dict:dict, lines_te:dict):
    total = 0
    correct = 0
    for key, values in lines_te.items():
        for value in values:
            total +=1
            bestPerplexity = inf
            bestKey = None
            padded_sent = pad_both_ends(list(value), N_GRAM)
            padded_sent = list(padded_sent)
            for key2, lm in lm_dict.items():
                bgr = list(everygrams(padded_sent, max_len = N_GRAM))
                # print(bgr)
                lm_perplexity = lm.perplexity(bgr)
                if (lm_perplexity < bestPerplexity):
                    bestPerplexity = lm_perplexity
                    bestKey = key2
            if bestKey == key:
                correct +=1
            # else:
            #     print(f"{value},{bestKey},{key}")
    print(f"LM Acc: {correct/total}")

def evaluate_NB(classifier,test_nb_data):
    accuracy = nltk.classify.util.accuracy(classifier, test_nb_data)
    print(f"NB Acc: {accuracy}")


if __name__ == "__main__":
    random.seed(100)
    corpus = "AlbatrossAndJeannette"
    train_path = "headers/{}/colHeaders.txt".format(corpus)
    classes_path = "headers/{}/colHeadersUniq.txt".format(corpus)
    output_path = "headers/{}/train/models/lm.pkl".format(corpus)
    lines = read_file(train_path)
    lines_tr, lines_te = train_test_split(lines,TRAIN_SIZE)

    headers_uniq = read_file(classes_path)
    classes_dict, classes_dict_inv = get_class_dic(headers_uniq)
    for k,v in classes_dict.items():
        print(k,"|||", classes_dict_inv.get(v))
    lines_tr, lines_dict_count_tr, total_tr = categorize_lines(lines_tr, classes_dict)
    lines_te, lines_dict_count_te, total_te = categorize_lines(lines_te, classes_dict)
    lines_dict_count_tr = {k:v/total_tr for k,v in lines_dict_count_tr.items()}
    for category, lines in lines_te.items():
        new_lines = [make_noise_str(line, NUM_NOISE) for line in lines]
        lines_te[category] = new_lines

    train_nb_data = get_NB_data(lines_tr)
    test_nb_data = get_NB_data(lines_te)

    lm_dict = train_lm(lines_tr,N_GRAM)
    classifier = NaiveBayesClassifier.train(train_nb_data)
    if TRAIN_SIZE == 1.0:
        lines_te = lines_tr
        test_nb_data = get_NB_data(lines_tr)
    else:
        test_nb_data = get_NB_data(lines_te)
    evaluate_lm(lm_dict, lines_te)
    evaluate_NB(classifier, test_nb_data)
    # classes_dict_inv = {v:k for k,v in classes_dict.items()}
    res = {
        "lm_dict": lm_dict,
        "ngram": N_GRAM,
        "classes_dict": classes_dict,
        "classes_dict_inv":classes_dict_inv,
        "priors": lines_dict_count_tr
    }

    with open(output_path, "wb") as fout:
        pickle.dump(res, fout)
    
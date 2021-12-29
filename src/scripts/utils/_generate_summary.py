import sys
from config.definitions import ROOT_DIR
import os
from tqdm import tqdm

from models.custom_dt import main as main1
from models.custom_nn import main as main2
from models.sklearn_dt import main as main3
from models.sklearn_svm import main as main4
from models.sklearn_knn import main as main5
from models.sklearn_random_forest import main as main6
from models.keras_nn import main as main7

SUMMARIES = {'custom_dt': main1, 
             'custom_nn': main2,
             'sklearn_dt': main3,
             'sklearn_svm': main4,
             'sklearn_knn': main5,
             'sklearn_random_forest': main6,
             'keras_nn': main7,
             }

def generate_summary():
    # load summaries to generate
    to_eval_path = os.path.join(ROOT_DIR, 'data', 'results', 'TO_EVAL.txt')
    with open(to_eval_path, 'r') as f:
        sum_names = [name.strip() for name in f.readlines()]

    # generate summaries
    for name in tqdm(sum_names):
        out_path = os.path.join(ROOT_DIR, 'data', 'results', f'{name}_output.txt')
        sys.stdout = open(out_path, 'w')
        SUMMARIES[name]()
        sys.stdout.close()

from functools import partial
import argparse
import os
import sys
import random
import time

sys.path.append('utils')
import numpy as np
import pandas as pd
from tqdm import tqdm
from paddle_serving_server.pipeline import PipelineClient
from data import gen_id2corpus
from utils.milvus_util import RecallByMilvus
from utils.config import collection_name, partition_tag


def search_in_milvus(text_embedding, corpus_file, query_text):
    client = RecallByMilvus()
    start_time = time.time()
    status, results = client.search(collection_name=collection_name,
                                    vectors=text_embedding,
                                    partition_tag=partition_tag)
    end_time = time.time()
    print('Search milvus time cost is {} seconds '.format(end_time -
                                                          start_time))
    id2corpus = gen_id2corpus(corpus_file)
    list_data = []
    for line in results:
        for item in line:
            idx = item.id
            distance = item.distance
            text = id2corpus[idx]
            list_data.append([query_text, text, distance])
    df = pd.DataFrame(list_data, columns=['query_text', 'label', 'distance'])
    df = df.sort_values(by="distance", ascending=True)
    for index, row in df.iterrows():
        print(row['query_text'], row['label'], row['distance'])


if __name__ == "__main__":
    client = PipelineClient()
    client.connect(['127.0.0.1:8080'])
    corpus_file = "data/label.txt"
    list_data = [{"sentence": "谈谈去西安旅游，哪些地方让你觉得不虚此行？"}]
    feed = {}
    for i, item in enumerate(list_data):
        feed[str(i)] = str(item)
    start_time = time.time()
    ret = client.predict(feed_dict=feed)
    end_time = time.time()
    print("Extract feature time to cost :{} seconds".format(end_time -
                                                            start_time))
    result = np.array(eval(ret.value[0]))
    search_in_milvus(result, corpus_file, list_data[0])

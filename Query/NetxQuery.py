import pandas as pd
import numpy as np
import networkx as nx
from networkx.drawing.nx_agraph import write_dot
import os
import csv
import math
import itertools as it


def query(queries_id):
    edges_df = pd.read_csv('edges_table.csv')
    edges_df = edges_df.drop_duplicates(subset=['source_id', 'target_id'], keep="first")
    G = nx.from_pandas_edgelist(edges_df, edge_attr=True, source="source_id", target="target_id", create_using=nx.DiGraph())

    output_num = math.factorial(len(queries_id))/(2*math.factorial((len(queries_id) - 2)))

    q_combinations = it.combinations(queries_id, 2)
    
    no_path=open("no_path.txt","w")


    stored_paths = {}
    for query_pair in q_combinations:
        source, target = query_pair
        try: 
            stored_paths[f"{source} -> {target}"] = nx.shortest_path(G, source, target)
        except nx.NetworkXNoPath:
            no_path.write(f"{source} -> {target} \n")
            pass
        except nx.NodeNotFound:
            pass

    query_nodes = {"Query_Ids": []}
    for key in stored_paths:
        for node in stored_paths[key]:
            query_nodes["Query_Ids"].append(node)

    query_nodes["Query_Ids"] = list(set(query_nodes["Query_Ids"]))

    query_nodes_df = pd.DataFrame.from_dict(query_nodes)


    # Gets the labels for a Query Id.
    nodes_df = pd.read_csv("nodes_table_all_labelled.csv", encoding="UTF-8")
    nodes_df = nodes_df.drop_duplicates(subset='Only_Id', keep="first")
    node_merged_df = pd.merge(nodes_df, query_nodes_df, how="inner", left_on="Only_Id", right_on="Query_Ids")[["Id", "Label", "Query_Ids"]]
    node_merged_df.columns = ["FullName", "Label", "Id"]


    expanded_paths = {}
    for key in stored_paths:
        breakdown_list = stored_paths[key]
        if breakdown_list != None:
            sub_pairings = []
            for i in range(0, len(breakdown_list) - 1):
                sub_pairings.append(tuple([breakdown_list[i], breakdown_list[i + 1]]))
            expanded_paths[key] = sub_pairings
        if breakdown_list == None:
            expanded_paths[key] = None

    # Create a dictionary for all pair interactions
    edges_merger = {
        "Source_Id": [],
        "Target_Id": []
    }
    for key in expanded_paths:
        for pair in expanded_paths[key]:
            edges_merger["Source_Id"].append(pair[0])
            edges_merger["Target_Id"].append(pair[1])


    edges_merger_df = pd.DataFrame.from_dict(edges_merger)
    edges_merger_df = edges_merger_df.drop_duplicates(subset=['Source_Id', 'Target_Id'], keep="first")
    edges_merged_df = pd.merge(edges_df, edges_merger_df, how="inner", left_on=["source_id", "target_id"], right_on=["Source_Id", "Target_Id"])
    edges_merged_df = edges_merged_df[["source", "source_id", "target", "target_id", "weight", "color_col", "thickness"]]
    edges_merged_df.columns = ["source_lab", "source", "target_lab", "target", "weight", "color_col", "thickness"]


    node_merged_df.to_csv("query_nodes.csv", index=False)
    edges_merged_df.to_csv("query_edges.csv", index=False)

import networkx as nx
import pandas as pd
import math
import itertools as it
import numpy as np

def query(G, edges_df, nodes_df, ev_df, queries_id, max_linkers):
    query_list = list(queries_id.values())

    edges_df = edges_df.drop_duplicates(subset=['source_id', 'target_id'], keep="first")

    li_perm = list(it.permutations(query_list, 2))
    q_combinations = [list(it.product(*sub_li)) for sub_li in li_perm]
    q_combinations = [item for sublist in q_combinations for item in sublist]


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
    print("Stored paths:", stored_paths)
    



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
    print("Expanded paths:", expanded_paths)
 

    deletion_keys = []

    for key in expanded_paths:
        i = 2
        if len(expanded_paths[key]) > max_linkers + 1:
            deletion_keys.append(key)

    for key in deletion_keys:
        del expanded_paths[key]
    print("Expanded paths after deletion:", expanded_paths)
    
    query_nodes = {"Query_Ids": []}
    for key in expanded_paths:
        for node in expanded_paths[key]:
            query_nodes["Query_Ids"].extend(node)

    query_nodes["Query_Ids"] = list(set(query_nodes["Query_Ids"]))
    print("Query nodes:", query_nodes)
    query_nodes_df = pd.DataFrame.from_dict(query_nodes)


    # Gets the labels for a Query Id.
    nodes_df = nodes_df.drop_duplicates(subset='Only_Id', keep="first")
    node_merged_df = pd.merge(nodes_df, query_nodes_df, how="inner", left_on="Only_Id", right_on="Query_Ids")[["Id", "Label", "Query_Ids"]]
    node_merged_df.columns = ["FullName", "Label", "Id"]
    
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

    edges_merged_df = edges_merged_df[["source", "source_id", "target", "target_id", "color_col", "thickness"]]
    edges_merged_df=pd.merge(edges_merged_df, ev_df, how="inner", on=["source_id","target_id"])[["source", "source_id", "target", "target_id", "color_col", "thickness", "evidence"]]
    edges_merged_df.columns = ["source_lab", "source", "target_lab", "target", "color_col", "thickness", "evidence"]

    
    #Data frame with which user query corresponds to which id
    name_df = pd.DataFrame([(key, var) for (key, L) in queries_id.items() for var in L], 
                 columns=['key', 'variable'])

    src = edges_merged_df[["source"]]
    merged_src = pd.merge(src, name_df, how="left", left_on="source", right_on = "variable")["key"]

    tar = edges_merged_df[["target"]]
    merged_tar = pd.merge(tar, name_df, how="left", left_on="target", right_on = "variable")["key"]

    
    #Convert IDs that correspond to a user query to the query name in query_nodes and query_edges
    edges_merged_df["source2"] = merged_src
    edges_merged_df["target2"] = merged_tar
    edges_merged_df["source_lab2"] = merged_src
    edges_merged_df["target_lab2"] = merged_tar
    edges_merged_df.source2.fillna(edges_merged_df.source, inplace=True)
    edges_merged_df.target2.fillna(edges_merged_df.target, inplace=True)
    edges_merged_df.source_lab2.fillna(edges_merged_df.source_lab, inplace=True)
    edges_merged_df.target_lab2.fillna(edges_merged_df.target_lab, inplace=True)
    edges_merged_df.drop(labels = ["source_lab", "source", "target_lab", "target"], axis=1, inplace=True)
    rename_dict = {"source_lab2":"source_lab", 
                  "target_lab2":"target_lab",
                  "source2":"source",
                  "target2":"target"}
    edges_merged_df = edges_merged_df.rename(columns=rename_dict)
    
    id_converted = pd.merge(node_merged_df, name_df, how="left", left_on="Id", right_on="variable")["key"]
    node_merged_df["Id2"] = id_converted
    node_merged_df["Label2"] = id_converted
    node_merged_df.Id2.fillna(node_merged_df.Id, inplace=True)
    node_merged_df.Label2.fillna(node_merged_df.Label, inplace=True)
    node_merged_df = node_merged_df.drop(labels = ["Label", "Id"], axis=1)
    rename_dict = {"Id2":"Id", 
                  "Label2":"Label"}
    node_merged_df = node_merged_df.rename(columns= rename_dict)
    
    #Get rid of the separator in the labels
    fixed_label = node_merged_df["Label"].str.replace("SPACE", " ")
    node_merged_df["Label"] = fixed_label
 
    node_merged_df.to_csv("query_nodes.csv", index=False)
    edges_merged_df.to_csv("query_edges.csv", index=False)
    


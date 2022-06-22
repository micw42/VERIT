import networkx as nx
import pandas as pd
import math
import itertools as it
import numpy as np
import copy

def query(G, edges_df, nodes_df, ev_df, queries_id, max_linkers, qtype, query_type, get_direct_linkers, db_df):
    nodes_df = nodes_df.drop_duplicates(subset='Id', keep="first")
    edges_df = edges_df.drop_duplicates(subset=['source', 'target'], keep="first")

    no_path=open("no_path.txt","w")
    
    if query_type == "name":
        query_list = list(queries_id.values())
        li_perm = list(it.permutations(query_list, 2))
        q_combinations = [list(it.product(*sub_li)) for sub_li in li_perm]
        q_combinations = [item for sublist in q_combinations for item in sublist]
        query_list_c = copy.deepcopy(query_list)
        query_list = [item for sublist in query_list for item in sublist]
        
    elif query_type == "id":
        query_list = queries_id["QUERY_ID"].split(",")
        q_combinations = list(it.permutations(query_list, 2))

    sources = list()
    targets = list()
    for query_pair in q_combinations:
        source, target = query_pair
        if qtype == "all_simple_paths":
            try:
                path = list(nx.all_simple_paths(G, source, target, cutoff=max_linkers))
                # Loop through interaction pairs in a path
                for ind in path:
                    for n1, n2 in zip(ind, ind[1:]):
                        sources.append(n1)
                        targets.append(n2)
            
            except nx.NetworkXNoPath:
                no_path.write(f"{source} -> {target} \n")
                pass
            
            except nx.NodeNotFound:
                pass

        elif qtype == "all_shortest_paths":
            try:
                path = list(nx.all_shortest_paths(G, source, target))
                
                for ind in path:
                    for n1, n2 in zip(ind, ind[1:]):
                        sources.append(n1)
                        targets.append(n2)


            except nx.NetworkXNoPath:
                no_path.write(f"{source} -> {target} \n")
                pass
            
            except nx.NodeNotFound:
                pass
            
    st_dict = {"source": sources, "target": targets}
    
    st_df = pd.DataFrame(st_dict).drop_duplicates()

    # Making edges
    rel_df = st_df.merge(edges_df, on=["source", "target"], how="left")

    # Bidirectional edges
    opp_df = rel_df.merge(edges_df, left_on=["source", "target"], right_on=["target","source"])
    opp_df = opp_df.drop(labels=["source_x","target_x","neg_color_x", 
                                 "pos_color_x", "inc_color_x", "thickness_x"], axis=1).rename(columns={"source_y":"source",
                                                                         "target_y":"target",
                                                                         "pos_color_y":"pos_color",
                                                                                                       "neg_color_y":"neg_color",
                                                                                                       "inc_color_y":"inc_color",
                                                                         "thickness_y":"thickness"})
    rel_df = pd.concat([rel_df, opp_df]).drop_duplicates(subset=["source", "target"])
    rel_df = rel_df.merge(ev_df, on=["source", "target"], how="left")[["source", "target", "pos_color", "neg_color", "inc_color", "thickness", "evidence"]]
    
    rel_df.to_csv("rel_df.csv", index=False)
    
    # Create nodes df
    nodes = list(it.chain(*q_combinations))
    nodes.extend(sources)
    nodes.extend(targets)
    nodes = list(set(nodes))
    nodes = pd.DataFrame({"Id": nodes})
    nodes = nodes.merge(nodes_df, on="Id", how="inner")[["Id", "Label"]]
    nodes = nodes.merge(db_df, left_on="Id", right_on="id", how="left")
    syn_concat = lambda x: "%%".join(x)
    aggregation_functions = {'Id': 'first', 'Label':"first", "name":syn_concat}
    nodes = nodes.groupby('id').aggregate(aggregation_functions)
    nodes.to_csv("internodes.csv", index=False)
    
    print("get_direct_linkers recursive", get_direct_linkers)
    found_ids = set(rel_df["source"].tolist()) | set(rel_df["target"].tolist()) - set(query_list)
    if get_direct_linkers:
        print("Getting direct linkers")
        links = edges_df[((edges_df["source_id"].isin(query_list)) & ~(edges_df["target_id"].isin(found_ids))) | 
                         ((edges_df["target_id"].isin(query_list)) & ~(edges_df["source_id"].isin(found_ids)))]
        links = links[links["thickness"] > 5]

        targets = links[(links["source_id"].isin(query_list)) & ~(links["target_id"].isin(query_list))]
        targets = targets[["target", "target_id", "source_id"]]
        sources = links[(links["target_id"].isin(query_list)) & ~(links["source_id"].isin(query_list))]
        sources = sources[["source", "source_id", "target_id"]]
        targets = targets.rename(columns = {"target":"FullName", "target_id":"Only_Id"})
        sources = sources.rename(columns = {"source":"FullName", "source_id":"Only_Id"})
        full_nodes = pd.concat([targets, sources]).drop_duplicates(subset = ["Only_Id"])
        full_nodes = full_nodes.merge(nodes_df, on = "Only_Id", how = "inner")
        full_nodes = full_nodes[["FullName", "Label", "Only_Id"]]
        full_nodes = full_nodes.rename(columns = {"Only_Id":"Id"})
        nodes = pd.concat([nodes, full_nodes])

        links = links.merge(ev_df, on=["source_id", "target_id"], how="left")[["source", "source_id", "target", "target_id", "color_col", "thickness", "evidence"]]
        links.columns = ["source_lab", "source", "target_lab", "target", "color_col", "thickness", "evidence"]
        rel_df = pd.concat([rel_df, links]).drop_duplicates(subset = ["source", "target"])

    
    #Fix the node labels to account for combined IDs
    if query_type == "name":
        name_df = pd.DataFrame([(key, var) for (key, L) in queries_id.items() for var in L], 
                 columns=['key', 'variable'])
        name_df.to_csv("name_df.csv", index=False)
        src = rel_df[["source"]]
        merged_src = pd.merge(src, name_df, how="left", left_on="source", right_on = "variable")["key"].tolist()
        tar = rel_df[["target"]]
        merged_tar = pd.merge(tar, name_df, how="left", left_on="target", right_on = "variable")["key"].tolist()
        rel_df["source2"] = merged_src
        rel_df["target2"] = merged_tar      
        rel_df.source2.fillna(rel_df.source, inplace=True)
        rel_df.target2.fillna(rel_df.target, inplace=True)
        rel_df.drop(labels = ["source", "target"], axis=1, inplace=True)
        rename_dict = {"source2":"source", "target2":"target"}
        rel_df = rel_df.rename(columns=rename_dict)
        
        id_converted = pd.merge(nodes, name_df, how="left", left_on="Id", right_on="variable")["key"]
        nodes["Id2"] = id_converted.tolist()
        nodes["Label2"] = id_converted.tolist()
        nodes.Id2.fillna(nodes.Id, inplace=True)
        nodes.Label2.fillna(nodes.Label, inplace=True)
        nodes = nodes.drop(labels = ["Label", "Id"], axis=1)
        rename_dict = {"Id2":"Id", 
                      "Label2":"Label"}
        nodes = nodes.rename(columns= rename_dict)
        
    # Combine synonyms in nodes with more than 1 ID
    syn_concat = lambda x: "%%".join(x)
    aggregation_functions = {"Label":"first", 'name': syn_concat}
    nodes = nodes.groupby("Id").aggregate(aggregation_functions).reset_index()
  
    # If used multiple IDs per query node, take the average of all edges
    rel_df = rel_df[["pos_color", "neg_color", "inc_color", "thickness", "evidence", "source", "target"]]
    rel_df["pos_color2"] = rel_df["pos_color"] * rel_df["thickness"]
    rel_df["neg_color2"] = rel_df["neg_color"] * rel_df["thickness"]
    rel_df["inc_color2"] = rel_df["inc_color"] * rel_df["thickness"]
    ev_concat = lambda x: "%%".join(x)
    aggregation_functions = {'pos_color2': 'sum', 'neg_color2': 'sum', 'inc_color2': 'sum', 'thickness': 'sum', 'evidence': ev_concat}
    rel_df = rel_df.groupby(["source", "target"]).aggregate(aggregation_functions).reset_index()
    rel_df["pos_color"] = rel_df["pos_color2"]/rel_df["thickness"]
    rel_df["neg_color"] = rel_df["neg_color2"]/rel_df["thickness"]
    rel_df["inc_color"] = rel_df["inc_color2"]/rel_df["thickness"]
    
    #For consistency: source and target columns disappear if dataframe is empty
    if len(rel_df.index)==0:
        rel_df = pd.DataFrame(columns=["pos_color", "neg_color", "inc_color",
                                       "thickness", "evidence", 
                                       "source", "target"])
        
    rel_df = rel_df[["pos_color", "neg_color", "inc_color", "thickness", "evidence", 
                     "source", "target"]]
    nodes = nodes[["Id", "Label", "name"]]
    if query_type == "name":
        nodes["Type"] = ["Query" if x in queries_id.keys() else ("Linker" if x in found_ids else "Direct") for x in nodes['Id']]   
    elif query_type == "id":
        nodes["Type"] = ["Query" if x in query_list else ("Linker" if x in found_ids else "Direct") for x in nodes['Id']]
        
    nodes["Label"] = nodes["Label"].str.replace("SPACE", " ")

    # Write edges and nodes
    nodes.to_csv("query_nodes.csv", index=False)
    rel_df.to_csv("query_edges.csv", index=False)
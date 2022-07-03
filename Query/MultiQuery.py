import networkx as nx
import pandas as pd
import math
import itertools as it
import numpy as np
import copy
import time

# queries_id: dict of format {query_name:[list of selected IDs]} (if name query)
# or {"QUERY_ID":"comma separated string of query IDs"} (if ID query)

# query_type: name or ID

#qtype: all_simple_paths or all_shortest_paths

def query(G, edges_df, nodes_df, ev_df, queries_id, max_linkers, qtype, query_type, get_direct_linkers, db_df):
    start = time.time()
    nodes_df = nodes_df.drop_duplicates(subset='Id', keep="first")
    edges_df = edges_df.drop_duplicates(subset=['source', 'target'], keep="first")
    
    no_path=open("no_path.txt","w")
    
    if query_type == "name":
        query_list = list(queries_id.values())
        # Get all possible pairs of queries (note: each query is a list of IDs)
        li_perm = list(it.permutations(query_list, 2)) 
        # Get all possible pairs of element from 1st list with element from 2nd list
        q_combinations = [list(it.product(*sub_li)) for sub_li in li_perm] 
        # Unroll to list of tuples
        q_combinations = [item for sublist in q_combinations for item in sublist]
        # Unroll list of query IDs
        query_list = [item for sublist in query_list for item in sublist]
        
    elif query_type == "id":
        query_list = queries_id["QUERY_ID"].split(",")
        q_combinations = list(it.permutations(query_list, 2))
    
    print(f"Checkpoint 1: {time.time() - start} sec")

    start = time.time()
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
                path = [x for x in path if (len(x)-1)<=max_linkers]
                for ind in path:
                    for n1, n2 in zip(ind, ind[1:]):
                        sources.append(n1)
                        targets.append(n2)


            except nx.NetworkXNoPath:
                no_path.write(f"{source} -> {target} \n")
                pass
            
            except nx.NodeNotFound:
                pass
            
    print(f"Querying: {time.time() - start} sec")
    
    start = time.time()
    
    st_dict = {"source": sources, "target": targets}
    
    st_df = pd.DataFrame(st_dict).drop_duplicates()

    # Making edges
    rel_df = st_df.merge(edges_df, on=["source", "target"], how="left")

    # Bidirectional edges
    opp_df = rel_df.merge(edges_df, left_on=["source", "target"], right_on=["target","source"])
    opp_df = opp_df.drop(labels=["source_x","target_x","color_x", "thickness_x"], axis=1).rename(columns={"source_y":"source", "target_y":"target", "color_y":"color", "thickness_y":"thickness"})
    rel_df = pd.concat([rel_df, opp_df]).drop_duplicates(subset=["source", "target"])
    
    # Create nodes df
    nodes = list(it.chain(*q_combinations)) # List of all query IDs
    # Add found nodes
    nodes.extend(sources)
    nodes.extend(targets)
    nodes = list(set(nodes))
    nodes = pd.DataFrame({"Id": nodes})
    nodes = nodes.merge(nodes_df, on="Id", how="inner")[["Id", "Label"]]
    
    # IDs that were found (not in original query list)
    found_ids = set(rel_df["source"].tolist()) | set(rel_df["target"].tolist()) - set(query_list)
    
    if get_direct_linkers:
        # Get all direct connections to query nodes that were not already found by query 
        # (user has option to show them in the visualization)
        links = edges_df[((edges_df["source"].isin(query_list)) & ~(edges_df["target"].isin(found_ids))) | 
                         ((edges_df["target"].isin(query_list)) & ~(edges_df["source"].isin(found_ids)))]

        # Filter thickness of direct connections so visualization isn't crowded (arbitrarily selected threshold)
        links = links[links["thickness"] > 20]  

        # Nodes directly targeted by query nodes
        targets = links[(links["source"].isin(query_list)) & ~(links["target"].isin(query_list))]
        targets = targets[["target"]]
        # Nodes that directly target query nodes
        sources = links[(links["target"].isin(query_list)) & ~(links["source"].isin(query_list))]
        sources = sources[["source"]]
        targets = targets.rename(columns = {"target":"Id"})
        sources = sources.rename(columns = {"source":"Id"})
        full_nodes = pd.concat([targets, sources]).drop_duplicates(subset = ["Id"])
        full_nodes = full_nodes.merge(nodes_df, on = "Id", how = "inner")
        full_nodes = full_nodes[["Id", "Label"]]

        # Add direct connection nodes to the rest of the nodes
        nodes = pd.concat([nodes, full_nodes])

        # Add direct connection edges to the rest of the edges
        rel_df = pd.concat([rel_df, links]).drop_duplicates(subset = ["source", "target"])
        
    print(f"Checkpoint 3: {time.time() - start} sec")
    
    start = time.time()
    rel_df = rel_df.merge(ev_df, on=["source", "target"], how="left")[["source", "target", "color", "thickness", "evidence"]]
    print(f"Evidence merge: {time.time() - start} sec")
        
    start = time.time()
    # Add synonyms to the nodes
    nodes = nodes.merge(db_df, left_on="Id", right_on="id", how="left")
    nodes["name"] = nodes["name"].fillna(nodes["Label"])
    nodes["id"] = nodes["id"].fillna(nodes["Id"])
    syn_concat = lambda x: "%%".join(x)  # Separate each synonym with %%
    aggregation_functions = {'Id': 'first', 'Label':"first", "name":syn_concat}
    nodes = nodes.groupby('id').aggregate(aggregation_functions)
    print(f"Checkpoint 4: {time.time() - start} sec")
    
    start = time.time()
    # Fix the node labels to account for combined IDs (can ignore)
    if query_type == "name":
        # Make df with user queries and corresponding IDs
        name_df = pd.DataFrame([(key, var) for (key, L) in queries_id.items() for var in L], 
                 columns=['key', 'variable'])
        
        # Fix edges table
        src = rel_df[["source"]]
        merged_src = pd.merge(src, name_df, how="left", left_on="source", right_on = "variable")["key"]
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
        
        # Fix nodes table
        id_converted = pd.merge(nodes, name_df, how="left", left_on="Id", right_on="variable")["key"]
        nodes["Id2"] = id_converted.tolist()
        nodes["Label2"] = id_converted.tolist()
        nodes.Id2.fillna(nodes.Id, inplace=True)
        nodes.Label2.fillna(nodes.Label, inplace=True)
        nodes = nodes.drop(labels = ["Label", "Id"], axis=1)
        rename_dict = {"Id2":"Id", 
                      "Label2":"Label"}
        nodes = nodes.rename(columns= rename_dict)
    
    print(f"Checkpoint 5: {time.time() - start} sec")
    
    start = time.time()
    # Combine synonyms again for nodes that were just fixed
    syn_concat = lambda x: "%%".join(x)
    aggregation_functions = {"Label":"first", 'name': syn_concat}
    nodes = nodes.groupby("Id").aggregate(aggregation_functions).reset_index()
  
    # For edges connecting nodes that correspond to multiple IDs, 
    # take average of all color values (weighted by thickness)
    
    rel_df = rel_df[["color", "thickness", "evidence", "source", "target"]]
    rel_df["color2"] = rel_df["color"] * rel_df["thickness"]
    ev_concat = lambda x: "%%".join(x) # Concat all evidence of edges connecting multiple-ID nodes
    aggregation_functions = {'color2': 'sum','thickness': 'sum', 'evidence': ev_concat}
    rel_df = rel_df.groupby(["source", "target"]).aggregate(aggregation_functions).reset_index()
    rel_df["color"] = rel_df["color2"]/rel_df["thickness"]
    
    #For consistency: source and target columns disappear if dataframe happens to be empty
    if len(rel_df.index)==0:
        rel_df = pd.DataFrame(columns=["color",
                                       "thickness", "evidence", 
                                       "source", "target"])
        
    rel_df = rel_df[["color", "thickness", "evidence", 
                     "source", "target"]]
    nodes = nodes[["Id", "Label", "name"]]
    
    # Indicate whether each node is query (part of user query list), 
    # linker (found by Netx algorithm), or direct (direct connection to query node not found by Netx)
    # For visualization 
    if query_type == "name":
        nodes["Type"] = ["Query" if x in queries_id.keys() else ("Linker" if x in found_ids else "Direct") for x in nodes['Id']]   
    elif query_type == "id":
        nodes["Type"] = ["Query" if x in query_list else ("Linker" if x in found_ids else "Direct") for x in nodes['Id']]
        
    nodes["Label"] = nodes["Label"].str.replace("SPACE", " ")
    
    # Remove recursive edges
    rel_df = rel_df[rel_df["source"] != rel_df["target"]]
    
    print(f"Checkpoint 6: {time.time() - start} sec")

    # Write edges and nodes
    nodes.to_csv("query_nodes.csv", index=False)
    rel_df.to_csv("query_edges.csv", index=False)
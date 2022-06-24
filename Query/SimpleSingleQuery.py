import pandas as pd
import copy

def query(G, edges_df, nodes_df, ev_df, query, depth):
    user_query = list(query.keys())[0]
    # For name queries (accounts for the user selecting multiple IDs)
    if user_query != "QUERY_ID":
        query_list = list(query.values())
        query_list = [item for sublist in query_list for item in sublist]
    # For ID queries
    else:
        query_list = list(query.values())

    # Recursively find target nodes
    # Go one depth further than selected depth to find any bidirectional connections of last layer
    targets = copy.deepcopy(query_list)
    full_df_cols = list(edges_df.columns)
    full_df_cols.append("depth")
    full_df = pd.DataFrame(columns = full_df_cols)
    for i in range(depth+1):
        query_df = edges_df[edges_df["source"].isin(targets)]
        query_df["depth"] = i+1
        targets = query_df["target"].drop_duplicates().tolist()
        full_df = full_df.append(query_df)
    
    # Drop the nodes in the outermost layer that are not connected to any inner nodes
    # Leaves only connections from last layer nodes to inner layer nodes
    inner_edges = full_df[full_df["depth"] != depth+1]
    outer_edges = full_df[full_df["depth"] == depth+1]
    inner_source = full_df[full_df["depth"] == depth]["source"].drop_duplicates().tolist()
    outer_edges = outer_edges[outer_edges["target"].isin(inner_source)]
    full_df = inner_edges.append(outer_edges)

    # Make query nodes depth = 0, so they're in the center of the visualization
    df_dict = {"target":query_list, "depth":[0]*len(query_list)}
    zero_rows = pd.DataFrame.from_dict(df_dict)
    # Only need the targets, since every node (except for some query nodes) are a target at least once
    unique_targets = full_df[["target", "depth"]].drop_duplicates(subset = "target", keep="first")
    nodes = zero_rows.append(unique_targets)
    nodes = nodes.drop_duplicates(subset = "target", keep="first") 
    nodes_df = nodes_df.drop_duplicates(subset='Id', keep="first")
    nodes = pd.merge(nodes, nodes_df, left_on = "target", right_on = "Id", how="inner")
    
    # If the user selected multiple IDs, merge them all into one node
    if user_query != "QUERY_ID":
        nodes.loc[(nodes.Id.isin(query_list)),'Label']=user_query
        nodes.loc[(nodes.Id.isin(query_list)),'Id']=user_query
        nodes = nodes.drop_duplicates(subset="Id")
    
    #Add evidence column to edges df
    full_df = full_df.drop_duplicates(subset=["source", "target"])
    ev_df = ev_df.drop_duplicates(subset=["source", "target"])
    full_df = pd.merge(full_df, ev_df, on=["source", "target"], how="inner")
    if user_query != "QUERY_ID":
        full_df.loc[(full_df.source.isin(query_list)),'source']=user_query
        full_df.loc[(full_df.target.isin(query_list)),'target']=user_query
    
    nodes = nodes[["Id", "Label", "depth"]]
    full_df = full_df[["pos_color", "neg_color", "inc_color", "thickness", "evidence", "source", "target"]]

    full_df.to_csv("query_edges.csv", index=False)
    nodes.to_csv("query_nodes.csv", index=False)
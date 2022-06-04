import pandas as pd
import copy

def query(G, edges_df, nodes_df, ev_df, query, depth):
    user_query = list(query.keys())[0]
    if user_query != "QUERY_ID":
        query_list = list(query.values())
        query_list = [item for sublist in query_list for item in sublist]
    else:
        query_list = list(query.values())

    
    
    targets = copy.deepcopy(query_list)
    full_df_cols = list(edges_df.columns)
    full_df_cols.append("depth")
    full_df = pd.DataFrame(columns = full_df_cols)
    for i in range(depth+1):
        query_df = edges_df[edges_df["source_id"].isin(targets)]
        query_df["depth"] = i+1
        targets = query_df["target_id"].drop_duplicates().tolist()
        full_df = full_df.append(query_df)
    
    #Drop the nodes in the outermost layer that are not connected to any inner nodes
    inner_edges = full_df[full_df["depth"] != depth+1]
    outer_edges = full_df[full_df["depth"] == depth+1]
    inner_source = full_df[full_df["depth"] == depth]["source_id"].drop_duplicates().tolist()
    outer_edges = outer_edges[outer_edges["target_id"].isin(inner_source)]
    full_df = inner_edges.append(outer_edges)

    #Add depth column to query nodes 
    df_dict = {"target_id":query_list, "depth":[0]*len(query_list)}
    zero_rows = pd.DataFrame.from_dict(df_dict)
    unique_targets = full_df[["target_id", "depth"]].drop_duplicates(subset = "target_id", keep="first")
    nodes = zero_rows.append(unique_targets)
    nodes = nodes.drop_duplicates(subset = "target_id", keep="first")
    nodes_df = nodes_df.drop_duplicates(subset='Only_Id', keep="first")
    nodes = pd.merge(nodes, nodes_df, left_on = "target_id", right_on = "Only_Id", how="inner")
    if user_query != "QUERY_ID":
        nodes.loc[(nodes.Only_Id.isin(query_list)),'Label']=user_query
        nodes.loc[(nodes.Only_Id.isin(query_list)),'Only_Id']=user_query
        nodes = nodes.drop_duplicates(subset="Only_Id")
    
    #Add evidence column to edges df
    full_df = full_df.drop_duplicates(subset=["source_id", "target_id"])
    ev_df = ev_df.drop_duplicates(subset=["source_id", "target_id"])
    full_df = pd.merge(full_df, ev_df, on=["source_id", "target_id"], how="inner")
    if user_query != "QUERY_ID":
        full_df.loc[(full_df.source_id.isin(query_list)),'source_id']=user_query
        full_df.loc[(full_df.target_id.isin(query_list)),'target_id']=user_query
    
    nodes = nodes[["Id", "Only_Id", "Label", "depth"]]
    full_df = full_df[["color_col", "thickness", "evidence", "source_id", "target_id"]]

    full_df.to_csv("query_edges.csv")
    nodes.to_csv("query_nodes.csv")
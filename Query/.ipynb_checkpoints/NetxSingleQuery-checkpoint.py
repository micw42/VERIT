import networkx as nx
import pandas as pd

#Makes a pandas dataframe from a netx object
def df_from_nx(T):
    source_ids=[]
    target_ids=[]
    thicknesses=[]
    color_cols=[]
    for edge in T.edges:
        source_ids.append(edge[0])
        target_ids.append(edge[1])
        thicknesses.append(T.edges[edge[0], edge[1]]["thickness"])
        color_cols.append(T.edges[edge[0], edge[1]]["color_col"])
        
    edges_dict={"source_id":source_ids, "target_id":target_ids, "thickness":thicknesses, "color_col":color_cols}
    
    query_edges=pd.DataFrame.from_dict(edges_dict)
    return query_edges


def nx_dfs(G, edges_df, query, depth, thickness_bound1, thickness_bound2):
    
    #Find all the immediate connections to the query node
    T=nx.dfs_tree(G, source=query, depth_limit=1)

    #Add edge attributes back into the DFS results
    for edge in T.edges:
            T.edges[edge[0], edge[1]]["color_col"]=G.get_edge_data(edge[0],edge[1])['color_col']
            T.edges[edge[0], edge[1]]["thickness"]=G.get_edge_data(edge[0],edge[1])['thickness']
    
    #Convert query results from netx object to pandas dataframe
    full_df=df_from_nx(T)
    
    #Drop rows with low literary presence
    full_df.drop(full_df[full_df['thickness'] < thickness_bound1].index, inplace = True)
    
    #Indicate that these rows were found at the first depth
    full_df["depth"]=1

    #The list of nodes to do DFS on next
    next_rows=full_df["target_id"].tolist()
    
    #To make sure we do not do DFS on a node more than once
    already_traversed=["GO:0044838"]

    for i in range(depth-1):
        loop_df=pd.DataFrame(columns=["source_id","target_id","thickness","color_col","depth"])

        for row in next_rows:
            T=nx.dfs_tree(G, source=row, depth_limit=1)
            for edge in T.edges:
                T.edges[edge[0], edge[1]]["color_col"]=G.get_edge_data(edge[0],edge[1])['color_col']
                T.edges[edge[0], edge[1]]["thickness"]=G.get_edge_data(edge[0],edge[1])['thickness']
            
            #The immediate connections to the node whose ID is specified by row
            row_df=df_from_nx(T)
            row_df["depth"]=i+2
            row_df.drop(row_df[row_df['thickness'] < thickness_bound2].index, inplace = True)
            loop_df=loop_df.append(row_df)
            already_traversed.append(row)
                               
        #Update the next set of nodes to do DFS on
        next_rows=list(set(loop_df["target_id"].tolist())-set(already_traversed))
        
        #Update the original dataframe
        full_df=full_df.append(loop_df)
        
    #Get reverse edges by inner join with edges_df
    reverse=pd.merge(full_df, edges_df, how="inner", left_on=["source_id","target_id"], right_on=["target_id", "source_id"])[["source_id_y","target_id_y","color_col_y","thickness_y"]]
    reverse.columns=["source_id","target_id","color_col","thickness"]
    full_df=full_df.append(reverse)
    full_df=full_df.drop_duplicates(subset=["source_id","target_id"])
        
    return full_df

def query(G, edges_df, nodes_df, ev_df, query, depth, thickness_bound1, thickness_bound2):
    
    full_df=nx_dfs(G, edges_df, query, depth, thickness_bound1, thickness_bound2)
    
    #Set the depth of the query node to 0
    node_depths={"Id":[query], "depth":[0]}
    node_depths=pd.DataFrame.from_dict(node_depths)
    
    #Get the first depth that the other nodes were found at
    target_depths=pd.DataFrame.from_dict({"Id":full_df["target_id"].tolist(), "depth":full_df["depth"].tolist()})
    node_depths=node_depths.append(target_depths)
    node_depths=node_depths.drop_duplicates(subset="Id", keep="first")

    # Gets the labels for a Query Id.
    nodes_df = nodes_df.drop_duplicates(subset='Only_Id', keep="first")
    node_merged_df = pd.merge(nodes_df, node_depths, how="inner", left_on="Only_Id", right_on="Id")[["Only_Id", "Label", "depth"]]
    node_merged_df.columns = ["Id", "Label", "depth"]
    
    #Get evidence for the edges
    full_df_ev=pd.merge(full_df, ev_df, how="inner", on=["source_id","target_id"])[["source_id","target_id","color_col","thickness","evidence"]]

    # Rename columns to be consistent with other query scripts
    full_df.columns = ["source", "target", "color_col", "thickness", "depth"]

    # Writes the tables out into a csv
    full_df_ev.to_csv("query_edges.csv", index=False)
    node_merged_df.to_csv("query_nodes.csv", index=False)
    
    
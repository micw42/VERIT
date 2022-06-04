import pandas as pd
import networkx as nx
from operator import add

#Find the length of the shortest path between ids
def path_length(G, query_id, other_id):
    try:
        path = nx.shortest_path(G, query_id, other_id)
        return len(path)
    except nx.NetworkXNoPath:
        return 10  #Large number to penalize not having a path
    except nx.NodeNotFound:
        #If we delete the nodes that aren't in edges_table, we won't need this
        return 0 
        

#Find average path lengths between a list of query ids and the other ids in the network
def avg(query_ids, other_ids, G):
    avg_list = []
    for i in range(len(query_ids)):
        source_lengths = [path_length(G, query_ids[i], other_id) for other_id in other_ids]
        target_lengths = [path_length(G, other_id, query_ids[i]) for other_id in other_ids]
        lengths = list(map(add, source_lengths, target_lengths))
        lengths = [length/2 for length in lengths]
        avg_list.append(sum(lengths)/len(lengths))
    return avg_list

def get_avg_col(user_queries, result, G):
    avg_col = []
    for query in user_queries:
        query_ids = result[result["user_query"] == query]["id"].tolist() #The ids returned by a user query
        other_ids = result[result["user_query"] != query]["id"].tolist() #The other ids in the network
        avg_list = avg(query_ids, other_ids, G)
        avg_col.extend(avg_list)
        #Progress tracker
        print("done with", query)
    return avg_col


#Find the total thickness and number of edges for a subset of IDs
def clean(subset_df, group_by):
    thickness_sum = subset_df.groupby([group_by], axis=0, as_index=False).sum()
    thickness_count = subset_df.groupby([group_by], axis=0, as_index=False).count()
    cleaned = thickness_sum.merge(thickness_count, how="inner", on=group_by)
    cleaned = cleaned[[group_by, "thickness_x", "source"]]
    cleaned = cleaned.rename(columns={group_by: "id", "thickness_x": "total_thickness", "source":"degree"})
    return cleaned

#Get the degree and total thickness of edges between user query ids and other ids in net
def get_relevance(user_query, edges_df, result):
    df_dict = {"id":[],
          "total_source_thickness":[],
          "source_deg":[],
          "total_target_thickness":[],
          "target_deg":[],
          "user_query":[]}
    new_df = pd.DataFrame.from_dict(df_dict)
    
    #Get the ids returned by the user query
    query_ids = result[result["user_query"]==user_query]["id"].tolist()
    #Get the other ids
    other_ids = result[result["user_query"] != user_query]["id"].tolist()
    #Get the edges where source is user query id, target is other id
    as_src_subset = edges_df[(edges_df["source_id"].isin(query_ids)) & (edges_df["target_id"].isin(other_ids))]
    #Get the edges where source is other id, target is user query id
    as_tar_subset = edges_df[(edges_df["source_id"].isin(other_ids)) & (edges_df["target_id"].isin(query_ids))]
    
    src_cleaned = clean(as_src_subset, "source_id")
    tar_cleaned = clean(as_tar_subset, "target_id")
    merged = src_cleaned.merge(tar_cleaned, how="outer", on="id")
    merged[["total_thickness_x","degree_x", "total_thickness_y", "degree_y"]] = merged[["total_thickness_x","degree_x", "total_thickness_y", "degree_y"]].fillna(0)
    rename_dict = {"total_thickness_x":"total_source_thickness", 
                  "degree_x":"source_deg",
                  "total_thickness_y":"total_target_thickness",
                  "degree_y":"target_deg"}
    merged = merged.rename(columns=rename_dict)
    query_col = [user_query] * len(merged.index)
    merged["user_query"] = query_col
    new_df = new_df.append(merged)
    return new_df

def reduce_result(query_list, edges_df, result):
    df_dict = {"id":[],
      "total_source_thickness":[],
      "source_deg":[],
      "total_target_thickness":[],
      "target_deg":[],
      "user_query":[]}
    new_df = pd.DataFrame.from_dict(df_dict)
    
    for query in query_list:
        rel_df = get_relevance(query, edges_df, result)
        new_df = new_df.append(rel_df)
        
    return new_df

#Calculate the average thickness of the edges that connect an ID to the rest of the IDs in the network
def avg_thickness(query_list, edges_df, result):
    reduced = reduce_result(query_list, edges_df, result)
    reduced['total_thickness'] = reduced['total_source_thickness']+reduced['total_target_thickness']
    reduced["total_deg"] = reduced["source_deg"]+reduced["target_deg"]
    reduced["avg_thickness"] = reduced['total_thickness']/reduced["total_deg"]
    reduced = reduced[["id", "user_query", "avg_thickness"]]
    return reduced

#Combine the dfs and calculate the metric 
def calculate_metric(result, user_queries, edges_df, G):
    user_queries = [x.lower() for x in user_queries]
    
    #Get unique ids from the results
    unique_ids = result.drop_duplicates(subset = ["id", "user_query"])
    #Get the average path lengths
    avg_col = get_avg_col(user_queries, unique_ids, G)
    
    unique_ids["avg_path_len"] = avg_col
    
    #Get the average thicknesses
    thickness_df = avg_thickness(user_queries, edges_df, unique_ids)
    
    #Join the path length and thickness dataframes
    merged = pd.merge(thickness_df, unique_ids, on=["id", "user_query"], how="outer") 
    merged[["avg_thickness"]] = merged[["avg_thickness"]].fillna(0)
    
    #Calculate the metric (avg_thickness + 1/avg_path_len)
    merged["metric"] = merged["avg_thickness"]+ 1/merged["avg_path_len"]
    
    #Drop name column b/c it's unnecessary
    merged = merged.drop(labels = ["name"], axis=1)
    final_df = pd.merge(merged, result, on=["id", "user_query"])
    final_df = final_df.sort_values(by = ["user_query", "metric", "id"], ascending=False)
    final_df.to_csv("multiSearchOutRanked.csv", index=False)

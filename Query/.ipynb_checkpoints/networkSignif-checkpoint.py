import pandas as pd

#Get thickness and degree of nodes in a subset of edges_df
def get_stats(subset_df, group_by):
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
    
    src_cleaned = get_stats(as_src_subset, "source_id")
    tar_cleaned = get_stats(as_tar_subset, "target_id")
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
        
    
def write_out(edges_df):
    result = pd.read_csv("multiSearchOut.csv")
    query_list = list(set(result["user_query"].tolist()))
    reduced = reduce_result(query_list, edges_df, result)
    merged = result.merge(reduced, on="id", how="inner")[["name", "id", "user_query_x"]]
    merged = merged.rename(columns = {"user_query_x":"user_query"})
    merged.to_csv("merged_out.csv")
    reduced = reduced.T
    reduced.columns = reduced.iloc[0]
    reduced = reduced.drop(["id"])
    reduced.to_csv("reduced_ids.csv", index=False)
    
    
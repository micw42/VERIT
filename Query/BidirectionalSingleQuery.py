
import pandas as pd

# Depth of 1 is recommended. This will identify nodes 1 intermediate away. So, (query node) -> (intermediate) -> (last node). If targeting a specific path, it is recommended to re-query with the intermediate/last output node in mind, else, runtime becomes vastly higher. Adjust the thickness_bound to adjust the amount of nodes output.
# Test query (covid): mesh:C000657245
def query(query, depth, thickness_bound):



    # This function returns the edge values for the query appearing in the source_id column. The query is both the initial query and subsequent intermediate nodes.

    def edges_df_search(query, thickness_bound, depth):

        edges_df = pd.read_csv('edges_table.csv')
        edges_df = edges_df.drop_duplicates(subset=['source_id', 'target_id'], keep="first")

        # Turn query into a dataframe to inner join on
        input_dict = {"source_id": [str(query)]}
        query_df = pd.DataFrame.from_dict(input_dict)

        # Find only rows with query as source
        all_query = pd.merge(edges_df, query_df, how="inner", on="source_id")


        # Drop rows with low literary presence
        all_query.drop(all_query[all_query['thickness'] < thickness_bound].index, inplace = True)
        all_query.reset_index(drop=True, inplace=True)


        #Find any reverse connections between the target nodes and the query
        targets=all_query["target_id"]
        targets.name="source_id"
        merged_targets=pd.merge(edges_df, targets, how="inner", on="source_id")
        reverse=merged_targets[merged_targets["target_id"]==query]

        #Append reverse onto all_query
        all_query=all_query.append(reverse)

        all_query["depth"] = [depth] * all_query.shape[0]

        return all_query


    '''
    query: an ID to begin the visualization from.
    depth: how many iterations outwards from the central query node.
    thickness_bound: threshold of literary mentions for all pairs
    return is in the form of 2 csv files.
    '''
    def single_querier(query, depth, thickness_bound):
        # Read in edges table
        edges_df = pd.read_csv('edges_table.csv')
        edges_df = edges_df.drop_duplicates(subset=['source_id', 'target_id'], keep="first")

        full_df = edges_df_search(query, thickness_bound, 1)
        

        # Iterates according to depth for additional node pairings
        for i in range(depth):
            # Initialize the dataframe to be looped through
            loop_df = pd.DataFrame(columns=["source", "source_id", "target", "target_id", "color_col", "thickness","depth"])

            # If on loop 1, just loop through the initialized full_df
            if i == 0:
                # For each controller of each input, find their next linker
                for _, target_id in full_df["target_id"].iteritems():
                    temp_df = edges_df_search(target_id, thickness_bound, i + 2)
                    # Update looper_df with the temp
                    loop_df = pd.concat([loop_df, temp_df]).reset_index(drop=True)

                # Update full_df with the loop_df
                full_df = pd.concat([full_df, loop_df]).reset_index(drop=True)
                # Create new dataframe that stores last depth loop
                prev_loop_df = loop_df

            # If at higher depth, use last iteration's store to loop through.
            else:
                for _, target_id in prev_loop_df["target_id"].iteritems():
                    temp_df = edges_df_search(target_id, thickness_bound, i + 1)
                    loop_df = pd.concat([loop_df, temp_df]).reset_index(drop=True)

                full_df = pd.concat([full_df, loop_df]).reset_index(drop=True)
                prev_loop_df = loop_df

        # Get all nodes from the produced subsetted edge table
        source_nodes = full_df["source_id"].tolist()
        target_nodes = full_df["target_id"].tolist()
        node_ids = list(set(source_nodes + target_nodes))
        query_nodes = {"Query_Ids": node_ids}
        query_nodes_df = pd.DataFrame.from_dict(query_nodes)

        #Get node depths
        node_depths={"Id":[query], "depth":[0]}
        node_depths=pd.DataFrame.from_dict(node_depths)
        target_depths=pd.DataFrame.from_dict({"Id":full_df["target_id"].tolist(), "depth":full_df["depth"].tolist()})
        node_depths=node_depths.append(target_depths)
        node_depths=node_depths.drop_duplicates(subset="Id", keep="first")

        # Gets the labels for a Query Id.
        nodes_df = pd.read_csv("nodes_table_all_labelled.csv", encoding="UTF-8")
        nodes_df = nodes_df.drop_duplicates(subset='Only_Id', keep="first")
        node_merged_df2 = pd.merge(nodes_df, node_depths, how="inner", left_on="Only_Id", right_on="Id")[["Only_Id", "Label", "depth"]]
        node_merged_df2.columns = ["Id", "Label", "depth"]

        # Rename columns to be consistent with other query scripts
        full_df.columns = ["source_lab", "source", "target_lab", "target", "color_col", "thickness", "depth"]

        # Writes the tables out into a csv
        full_df.to_csv("query_edges.csv", index=False)
        node_merged_df2.to_csv("query_nodes.csv", index=False)

    single_querier(query, depth, thickness_bound)


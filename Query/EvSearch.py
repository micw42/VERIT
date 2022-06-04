import pandas as pd

def get_ev():
    # The edges table to find evidence from. Reads "source" and "target" columns which must each contain only IDs.
    input_edges = "query_edges.csv"

    def get_evidence(edges_table_df, ev_id_df):
        edges_id_cols = edges_table_df[["source", "target"]]
        edges_id_dict = edges_id_cols.to_dict()
        edges_id_dict["LONG_EVIDENCE"] = []

        # len(edges_id_dict["source_id"])
        for i in range(len(edges_id_dict["source"])):
            # Finds the single pair's matches in the evidence dataframe (SLOW)
            out_id = edges_id_dict["source"][i]
            cont_id = edges_id_dict["target"][i]
            query_ev = ev_id_df.query('(OUTPUT_ID==@out_id) & (CONTROLLER_ID==@cont_id)').reset_index(drop=True)

            # Creates a long string of all evidence
            evidence_concat = str()
            j = 0
            for j in range(len(query_ev["OUTPUT_ID"])):
                pmcid_add = " (" + query_ev["SEEN_IN"][j] + ")"
                evidence_concat += query_ev["EVIDENCE"][j] + pmcid_add + "|" + query_ev["EVENT_LABEL"][j] + "|%%"

            # Adds the entire concatenated string as a column's entry
            edges_id_dict["LONG_EVIDENCE"].append(evidence_concat)

        edges_id_dict["LONG_EVIDENCE"] = pd.Series(edges_id_dict["LONG_EVIDENCE"])
        edges_ev_df = pd.DataFrame(edges_id_dict)
        return edges_ev_df


    edges_table_df = pd.read_csv(input_edges, encoding="utf-8")
    ev_id_df = pd.read_csv("AllActNC.csv", encoding='utf-8')

    query_edges_ev_df = get_evidence(edges_table_df, ev_id_df)
    new_edge_df = pd.merge(edges_table_df, query_edges_ev_df, on=["source", "target"], how="left")

    new_edge_df.to_csv("query_edges_ev.csv")
import pandas as pd
import numpy as np


def clean_nodes():

    nodes_df=pd.read_csv("query_nodes.csv",header = 0)

    #Duplicate the depth column in nodes table
    nodes_df["rank"]=nodes_df["depth"]

    #Convert rank values so small values are large and vice versa
    def get_rank_value(rank):
        if rank==0:
            return 1000000000
        elif rank==1:
            return 1000000
        elif rank==2:
            return 10000
        elif rank==3:
            return 1000
        elif rank==4:
            return 1

    nodes_df["rank"]=nodes_df["rank"].apply(get_rank_value)


    #Convert depth to color in nodes table
    def get_node_color(depth):
        if depth==0:
            return "#fc0800"
        elif depth==1:
            return "#f1c9f2"
        elif depth==2:
            return "#c9ddf2"
        elif depth==3:
            return "#d7f2c9"
        else:
            return "#f7d4ab"

    nodes_df["depth"]=nodes_df["depth"].apply(get_node_color)

    return nodes_df

def clean_edges():

    edges_df=pd.read_csv("query_edges.csv",header = 0)

    #Take square root of thickness column so values aren't too big
    edges_df["thickness"]=5*np.sqrt(edges_df["thickness"])

    #Convert the color col into hex color strings
    def get_color(color_val):
        if float(color_val)<.1:
            return "#ff0000"
        elif float(color_val)<.2:
            return "#ff4545"
        elif float(color_val)<.3:
            return "#ff7a7a"
        elif float(color_val)<.4:
            return "#ffb0b0"
        elif float(color_val)<.5:
            return "#ffffff"
        elif float(color_val)<.6:
            return "#dbe8ff"
        elif float(color_val)<.7:
            return "#99beff"
        elif float(color_val)<.8:
            return "#669eff"
        elif float(color_val)<.9:
            return "#2b79ff"
        return "#005eff"

    edges_df["color_col"]=edges_df["color_col"].apply(get_color)

    return edges_df

#Convert nodes and edges tables into one json-style list
def convert(nodes_df, edges_df):

    nodes=[]
    for _, row in nodes_df.iterrows():
        parts=row.values.tolist()
        nodes.append(parts)

    elements=[]
    for node in nodes:
        node_dict={"data":{"id":node[2], "label":node[3], "color":node[4], "rank":int(node[5])}}
        elements.append(node_dict)

    edges=[]
    for _, row in edges_df.iterrows():
        parts=row.values.tolist()
        edges.append(parts)

    for edge in edges:
        edge_id=edge[4]+edge[5]
        edge_dict={"data":{"id":edge_id, "source":edge[4], "target":edge[5], "weight":edge[2], "color":edge[1], "ev":edge[3]}}
        elements.append(edge_dict)


    return elements

def clean():
    nodes_df=clean_nodes()
    edges_df=clean_edges()
    elements=convert(nodes_df, edges_df)
    return elements












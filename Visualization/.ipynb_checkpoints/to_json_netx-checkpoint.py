import pandas as pd
import numpy as np
import math

def clean_nodes():

    nodes_df=pd.read_csv("query_nodes.csv",header = 0)
    
    def get_color(query_type):
        if query_type == "Query":
            return "#fc0800"
        else:
            return "#99beff"
        
    def get_class(query_type):
        if query_type == "Query":
            return "level3"
        else:
            return "level0"
    
    nodes_df["Color"] = nodes_df["Type"].apply(get_color)
    nodes_df["class"] = nodes_df["Type"].apply(get_class)

    return nodes_df

def clean_edges():

    edges_df=pd.read_csv("query_edges.csv",header = 0)
    
    def get_width(x):
        if x<50:
            return x+10
        else:
            return math.log(x,10)+60

    #Take square root of thickness column so values aren't too big
    edges_df["edge_width"]=edges_df["thickness"].apply(get_width)

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

def get_square_clusters():
    nodes_df=pd.read_csv("query_nodes.csv",header = 0)
    is_query = nodes_df[nodes_df["Type"] == "Query"]["Id"].tolist()
    linkers = nodes_df[nodes_df["Type"] == "Linker"]["Id"].tolist()
    direct = nodes_df[nodes_df["Type"] == "Direct"]["Id"].tolist()
    side_len = int(math.sqrt(len(linkers)))
    if len(linkers) == 0:
        align = [{"nodeId": is_query[i], "position": {"x": 1000*(i%2), "y": 1000*(i//2)}} for i in range(len(is_query))]
    else:
        align = [{"nodeId": is_query[i], "position": {"x": (side_len*500+5000)*(i%2), "y": (side_len)*100*(i//2+1)}} for i in range(len(is_query))]
    y_coord = 0
    x_coord = 2500
    for i in range(len(linkers)):
        align.append({"nodeId":linkers[i], "position":{"x":x_coord, "y":y_coord}})
        x_coord += 500
        if i%side_len == 0:
            x_coord = 2500
            y_coord += 500
    print(align)
    return align


#original function
def get_orig_clusters():
    nodes_df=pd.read_csv("query_nodes.csv",header = 0)
    is_query = nodes_df[nodes_df["Type"] == "Query"]["Id"].tolist()
    linkers = nodes_df[nodes_df["Type"] == "Linker"]["Id"].tolist()
    direct = nodes_df[nodes_df["Type"] == "Direct"]["Id"].tolist()
    if len(linkers) == 0:
        align = [{"nodeId": is_query[i], "position": {"x": 1000*(i%2), "y": 1000*(i//2)}} for i in range(len(is_query))]
    else:
        align = [{"nodeId": is_query[i], "position": {"x": 10000*(i%2), "y": 10000*(i//2)}} for i in range(len(is_query))]
    align_linkers_n1 = [{"left": is_query[0], "right": x, "gap": 2500} for x in linkers]
    align_linkers_n2 = [{"left": x, "right": is_query[1], "gap": 2500} for x in linkers]
    align_linkers = align_linkers_n1 + align_linkers_n2
    return (align, align_linkers)   

#Convert nodes and edges tables into one json-style list
def convert(nodes_df, edges_df):

    nodes=[]
    for _, row in nodes_df.iterrows():
        parts=row.values.tolist()
        nodes.append(parts)

    elements=[]
    for node in nodes:
        print(node)
        print("Node syn:", node[4])
        node_dict={"data":{"id":node[1], "label":node[2], "type":node[4], "syn":node[3],
                           "color":node[5], "classes":node[6]}}
        print(node_dict)
        elements.append(node_dict)

    edges=[]
    for _, row in edges_df.iterrows():
        parts=row.values.tolist()
        edges.append(parts)
    
    for edge in edges:
        edge_id=edge[3]+edge[4]
        edge_dict={"data":{"id":edge_id, "source":edge[3], "target":edge[4], "weight":edge[7], "color":edge[0], "ev":edge[2], "thickness":edge[1]}}
        elements.append(edge_dict)

    return elements

def clean():
    nodes_df=clean_nodes()
    edges_df=clean_edges()
    return convert(nodes_df, edges_df)






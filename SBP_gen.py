import math
import random
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from collections import namedtuple, deque
from itertools import count
#from PIL import Image
import lzma
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from cache_env import read_prefetch_data,read_load_trace_data
from torch.utils.data import Dataset,DataLoader
from tqdm import tqdm
import sys

BLOCK_BITS=6
WINDOW_SIZE = 256
#PREF= 32 
def load_traces(path_cache, path_bo, path_spp, path_isb,path_domino, warm_up,total):
    df_miss_trace=read_load_trace_data(path_cache, warm_up,total)
    df_bo=read_prefetch_data(path_bo, warm_up,total)
    df_bo.columns=["id","bo"]
    df_spp=read_prefetch_data(path_spp, warm_up,total)
    df_spp.columns=["id","spp"]
    df_isb=read_prefetch_data(path_isb, warm_up,total)
    df_isb.columns=["id","isb"]
    df_domino=read_prefetch_data(path_domino, warm_up,total)
    df_domino.columns=["id","domino"]
    
    
    pd_cac=pd.merge(df_miss_trace,df_bo,on="id",how="left")
    pd_cac=pd.merge(pd_cac,df_spp,on="id",how="left")
    pd_cac=pd.merge(pd_cac,df_isb,on="id",how="left")
    pd_cac=pd.merge(pd_cac,df_domino,on="id",how="left")

    
    pd_cac["bo"]=pd_cac["bo"].astype('Int64')
    pd_cac["spp"]=pd_cac["spp"].astype('Int64')
    pd_cac["isb"]=pd_cac["isb"].astype('Int64')
    pd_cac["domino"]=pd_cac["domino"].astype('Int64')
    
    df=pd_cac.fillna(0)
    return df

def convert_blk_n_hex(pred_addr_blk):
    res=int(int(pred_addr_blk)<<(BLOCK_BITS))
    res2=res.to_bytes(((res.bit_length() + 7) // 8),"big").hex().lstrip('0')
    return res2

def select_action_gen(bo,spp,isb,domino):
    pick=np.argmax([bo,spp,isb,domino])
    return pick

def pick_addr(bo,spp,isb,domino,pick):
    if pick == 0:
        return bo
    elif pick == 1:
        return spp
    elif pick == 2:
        return isb
    elif pick == 3:
        return domino
    else:
        return 0
def output_pref_file(df,item,path):
    df["pref_hex"]=df.apply(lambda x: convert_blk_n_hex(x[item]),axis=1)
    df2=df[df["pref_hex"]!=""]
    df2[["id","pref_hex"]].to_csv(path,header=False, index=False, sep=" ")
    return

def output_partition(df,path):
    pick_dict={}
    pick_list=df["pick"].values.tolist()
    pick_dict["BO"]=[pick_list.count(0)]
    pick_dict["SPP"]=[pick_list.count(1)]
    pick_dict["ISB"]=[pick_list.count(2)]
    pick_dict["Domino"]=[pick_list.count(3)]
    df_pick=pd.DataFrame(pick_dict)
    df_pick.to_csv(path,header=True,index=False)
    return df_pick
#%%
'''
path_cache="/home/pengmiao/Disk/work/HPCA/ML-DPC-S0/LoadTraces/spec17/623.xalancbmk-s0.txt.xz"
path_bo="/home/pengmiao/Disk/work/HPCA/pref_trace/ALL_2_8/spec17/623.xalancbmk-s0.trace.xz.bo_file.txt"
path_spp="/home/pengmiao/Disk/work/HPCA/pref_trace/ALL_2_8/spec17/623.xalancbmk-s0.trace.xz.spp_file.txt"
path_isb="/home/pengmiao/Disk/work/HPCA/pref_trace/ALL_2_8/spec17/623.xalancbmk-s0.trace.xz.sisb_file.txt"     
path_domino="/home/pengmiao/Disk/work/HPCA/pref_trace/ALL_2_8/spec17/623.xalancbmk-s0.trace.xz.domino_file.txt"

#model_save_path="/home/pengmiao/Disk/work/HPCA/2_RL/results/spec17/623.xalancbmk-s0.trace.xz.pth"
path_prefetch_file_root = "/home/pengmiao/Disk/work/HPCA/4_Base_SBP/results/gen_pref_files/623.xalancbmk-s0.trace.xz."
path_partition="/home/pengmiao/Disk/work/HPCA/4_Base_SBP/results/partition/623.xalancbmk-s0.trace.xz."
'''
#%%
if __name__ == "__main__":   
    WARM=int(sys.argv[1])
    TOTAL=int(sys.argv[2])
    
    path_cache=sys.argv[3]
    path_bo=sys.argv[4]
    path_spp=sys.argv[5]
    path_isb=sys.argv[6]
    path_domino=sys.argv[7]

    path_prefetch_file_root=sys.argv[8]
    path_partition=sys.argv[9]
    
    access_buff=[]
    pref_bo=[]
    pref_spp=[]
    pref_isb=[]
    pref_domino=[]
    
    df = load_traces(path_cache, path_bo, path_spp, path_isb,path_domino, WARM,TOTAL)
    df_len=len(df)
    import pdb
    #pdb.set_trace()
    for index, row in df.iterrows():
        if index+WINDOW_SIZE+1<df_len:
            end=index+WINDOW_SIZE+1
        else:
            end = df_len-1
        access_buff=df["addr_blk"][index+1:end]
        hit = int(row["bo"] in access_buff.values)
        pref_bo.append(hit)
        hit = int(row["spp"] in access_buff.values)
        pref_spp.append(hit)
        hit = int(row["isb"] in access_buff.values)
        pref_isb.append(hit)
        hit = int(row["domino"] in access_buff.values)
        pref_domino.append(hit)
    
    df["bo_hit"]=pref_bo    
    df["spp_hit"]=pref_spp
    df["isb_hit"]=pref_isb
    df["domino_hit"]=pref_domino
    df[["bo_hit1","spp_hit1","isb_hit1","domino_hit1"]]=df[["bo_hit","spp_hit","isb_hit","domino_hit"]].rolling(WINDOW_SIZE).sum()
    df=df.fillna(0)
    df["pick"]=df.apply(lambda x: select_action_gen(x["bo_hit1"],x["spp_hit1"],x["isb_hit1"],x["domino_hit1"]),axis=1)    
    df["sbp"]=df.apply(lambda x: pick_addr(x["bo"],x["spp"],x["isb"],x["domino"],x["pick"]),axis=1)    
    
    output_pref_file(df,"sbp",path_prefetch_file_root+"sbp.pref.100.csv")
    output_partition(df,path_partition+"sbp.partition.100.csv")

    
    
    
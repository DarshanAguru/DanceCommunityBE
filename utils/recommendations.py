import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import warnings
from typing import List,Dict
from .dbConnect import connectDB
warnings.simplefilter(action='ignore', category=FutureWarning)


def mapClickCountToClass(clickTracks:List|List[List]):
        maindataDanceForms = dict()
        maindataClasses = dict()
        for val in clickTracks:
            dataDanceForms = dict()
            dataClasses = dict()    
            for click in val['clickTracks']:
                key1 = click['danceFormName']
                key2 = click['className']

                if dataClasses.get(key2, None) is None:
                    dataClasses[key2] = 1
                else:
                    dataClasses[key2] += 1

                if dataDanceForms.get(key1,None) is None:
                    dataDanceForms[key1] = 1
                else:
                    dataDanceForms[key1] +=1
            maindataDanceForms[str(val['_id'])]=dataDanceForms
            maindataClasses[str(val['_id'])]=dataClasses
            
        return  maindataDanceForms,maindataClasses
    
def getAllDfnsFreq(all_dfns:Dict,l:int):
    all_dfns_freq = dict()
    for k,v in all_dfns.items():
            if len([*v.values()]) < l:
                all_dfns_freq[k] = [*v.values(), *[0 for _ in range(l-len([*v.values()]))]]
            else:
                 all_dfns_freq[k] = [*v.values()]
    return all_dfns_freq




def dfnRecommender(df_dfn:pd.DataFrame,userId:str, n_neighbors:int, numRecs:int):
     df1 = df_dfn.copy()
     knn = NearestNeighbors(metric="cosine",algorithm="brute")
     knn.fit(df_dfn.values)
     distances,indices=knn.kneighbors(df_dfn.values,n_neighbors=n_neighbors)
     user_idx = df_dfn.columns.tolist().index(str(userId))
     for r,dn in list(enumerate(df_dfn.index)):
          if df_dfn.iloc[r,user_idx] == 0:
               sim_dfns= indices[r].tolist()
               dn_distances=distances[r].tolist()
               if r in sim_dfns:
                    id_dfn = sim_dfns.index(r)
                    sim_dfns.remove(r)
                    dn_distances.pop(id_dfn)
               else:
                    sim_dfns = sim_dfns[:n_neighbors-1]
                    dn_distances = dn_distances[:n_neighbors-1]
                
               dn_similarity = [1-x for x in dn_distances]
               dn_similarity_copy = dn_similarity.copy()
               nominator = 0
               
               for s in range(0,len(dn_similarity)):
                    if df_dfn.iloc[sim_dfns[s], user_idx] == 0:
                         if len(dn_similarity_copy) == (n_neighbors - 1):
                              dn_similarity_copy.pop(s)
                         else:
                              dn_similarity_copy.pop(s-(len(dn_similarity)-len(dn_similarity_copy)))
                    else:
                         nominator = nominator + dn_similarity[s]*df_dfn.iloc[sim_dfns[s], user_idx]

               if len(dn_similarity_copy) > 0:
                    if(sum(dn_similarity_copy)) > 0:
                         predicted_r=nominator/sum(dn_similarity_copy)
                    else:
                         predicted_r = 0
               else:
                    predicted_r = 0 
               df1.iloc[r,user_idx]=predicted_r   
     rec_dfns=[]
     res=dict()
     visited=[]
     for r in df_dfn[df_dfn[userId] > 0][userId].index.tolist():
        visited.append(r)
     res["visited"]=visited
     for r in df_dfn[df_dfn[userId] == 0].index.tolist():
          idx_df = df_dfn.index.tolist().index(r)
          predicted_rat = df1.iloc[idx_df,df1.columns.tolist().index(userId)]
          rec_dfns.append((r,predicted_rat))
     
     sorted_rm = sorted(rec_dfns, key=lambda x:x[1], reverse=True)
     rec = []
     for rec_m in sorted_rm[:numRecs]:
          rec.append(rec_m[0])
     res['recommended'] = rec
     return res
    
           

          


def getRecommendations(userId:str):
    try:
        db = connectDB()
        all_user_click_data = db.users.find(projection={"name":False, "pswd":False, "type":False, "email":False, "phone":False,"country":False,"state":False,"city":False})
        all_data_dfn, all_data_cl = mapClickCountToClass([x for x in all_user_click_data])
        dfns=db.classes.find(projection={"_id":False,"danceFormName":True})
        dfns= sorted(list(set([x['danceFormName'] for x in dfns])))
        all_dfns = getAllDfnsFreq(all_data_dfn,len(dfns))
        df_dfn = pd.DataFrame(all_dfns,index=dfns)
        n_neighbours = 3 if len(dfns)>2 else 2
        numRecs = 3 if len(dfns)>2 else 2
        movies = dfnRecommender(df_dfn,userId,n_neighbours,numRecs)
        return movies
        # print(movies)
    except Exception as e:
        print(e)
    
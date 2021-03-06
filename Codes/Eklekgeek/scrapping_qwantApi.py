# -*- coding: utf-8 -*-
"""
SCRIPT de WEBSCRAPING avec l'API QWANT du group Eklekgeek.

Conceptuellement ce script est très proche de celui de scraping de google/bing
"""


insee_proxies = {'http': 'http://proxy-rie.http.insee.fr:8080',
       'https': 'http://proxy-rie.http.insee.fr:8080'}
    
import re
import json
import requests
import logging
import pandas as pd
from urllib.parse import urlencode, urlparse, parse_qs
import http.client as http_client
from bs4 import BeautifulSoup
from pprint import pprint
import time


##MODE DEBUG
#http_client.HTTPConnection.debuglevel = 0
#logging.basicConfig()
#logging.getLogger().setLevel(logging.WARNING)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.WARNING)
#requests_log.propagate = True

#nbr d'echo max par requete
count = 10
url_search = 'https://api.qwant.com/egp/search/web?count='+str(count)

i =1
### Fonction pour écrire la page à chercher sur le moteur de recherche 
# - Remplacement espaces par + 
# Idée : input de cette fonction : concaténation des champs adresse et raison sociale de l'établissement


#input : l'url et les param de la requête
#output : reponse http
def get_request(url,param):
    """Fonction pour écrire la page à chercher."""
    # On spécifie les herders pour ce faire passer pour une utilisateur "normal", sinon
    # qwant renvoie un peu n'importe quoi
    headers = {'user-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'
#               ,'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
#               ,'Accept-Encoding' : 'gzip, deflate'
#               ,'Accept-Language	':'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3'
#               ,'Cache-Control' : 'max-age=0'
#               ,'Connection' : 'keep-alive'
#               ,'DNT':'1'
#               ,'Host'	:'api.qwant.com'
               }
    
    
    #On remplace les espaces par des +
    chaine_nettoyee = re.sub(' ', '+', param.strip())
    if param =="" : 
        chaine_nettoyee = url
    else:
         chaine_nettoyee = url+"&q="+chaine_nettoyee
         print(chaine_nettoyee)
    output = requests.get(chaine_nettoyee, proxies=insee_proxies, headers=headers)
    if output.status_code != 200:
        print(output.status_code)
        
        raise Exception
    else :
        return output

#Fichier output
# Pour éviter qu'une erreur nous fasse tout perdre, on va écrire régulièrement dans un fichier
# et vider les objets en mémoire
recensement = pd.read_csv("D:/S4LWO8/Mes Documents/hackathon/donnees rp/ech_qwant.csv", sep=";")
    
#Les données en entrée

#recensement_sample = recensement[:1000]
recensement_sample = recensement

    
# Création propre de la variable à mettre en entrée pour aller choper le siret
# On va concaténer "RS_X", "NUMVOI_X", "TYPEVOI_X","NOMVOI_X","CLT_X" pour la recheche
liste_colonnes = ["RS_X", "NUMVOI_X", "TYPEVOI_X","NOMVOI_X","CLT_X"]


recensement_sample = recensement_sample.fillna("")
libelle_etab = recensement_sample[liste_colonnes].applymap(
        lambda x: str(int(x)) if isinstance(x, (int, float)) else x
).apply(" ".join, axis = 1)

siret_final_array = recensement_sample['SIRET_DEC'].apply(
        lambda x: str(int(x)) if isinstance(x, (int, float)) else x
)
    
print(libelle_etab)
    
# Suppresion doubles espaces

libelle_etab = libelle_etab.apply(lambda x: re.sub("  +", " ", x))
cabbi_array = recensement_sample['CABBI']


    
#dict pour stoker les variables, forme clef:[valeurs]
#hash_etab={'cabbi' : [], 'Adresse' : [], 'Nom' : [], 'Complément de nom' : [], 'N° de SIRET': []
#                 , 'Ville' : [], 'Libellé du code APE' : []}
#info_etab = ['Adresse', 'Nom', 'Complément de nom', 'N° de SIRET'
#                 , 'Ville', 'Libellé du code APE']

output_finale = {'cabbi' : []
    , 'siret': []
    , 'siret_final' : []
    , 'is_equals' : []
    , 'position_page' : []
    , 'x_rp': []
    , 'y_rp': []
    , 'sourcexyw_rp': []
    , 'qualxy_rp': []
    , 'rs_rp' : []}
        
#On boucle sur nos etabablissement

i = 0
while i< len(libelle_etab):

    #Les pauses servent à éviter de faire trop de requête rapidement pour ne pas
    #se faire bloquer l'IP.
    time.sleep(1)
    
    #On initialise nos variables
    etab = libelle_etab[i]
    print("etab : " + str(etab))
    cabbi = recensement_sample['CABBI'][i]
    siret_final = siret_final_array[i]
    print ("cabbi =" + str(cabbi))
    X_RP = recensement_sample['x'][i]
    Y_RP = recensement_sample['y'][i]
    SourceXYW = recensement_sample['SourceXYW'][i]
    qual = recensement_sample['qual'][i]
    raison_sociale_declaree = recensement_sample['RS_X'][i]
    
    
    #Boucle pour s'assurer que la requête soit faite
    #On va la lancer tant qu'on a une exception en attendant 10 sec entre les tentatives
    #Problématique hackathon pour avoir des données à traiter
    boolean = True
    while boolean:
        try :
            response = get_request(url_search,"site:societe.com " + etab)
            boolean = False
        except Exception:
            time.sleep(10)
            print("pb")
    
    #on récupère un json
    req_json = response.json()
    array_href = []
    
#    les urls que l'on cherche sont dans data/result/item/url
#    pprint(req_json)
    #on parcours les item du json
    position = 1
    if 'data' in req_json:
    
        for item in req_json['data']['result']['items']:
            #contient l'url que l'on souhaite ?
    #        print(link.get('href'))
            item_url = item['url']
            print(item_url)
            if "https://www.societe.com/etablissement/" in item_url :
                #On regarde maintenant si 14 chiffres consécutifs
    #            print(link.get('href'))
                siret_trouve = re.findall("\d{14}", item_url)
                siret_propre = siret_trouve[0]
                
                output_finale['cabbi'].append(cabbi)
                output_finale['is_equals'].append(siret_propre==siret_final)
                output_finale['siret'].append(str(siret_propre))
                output_finale['position_page'].append(position)
                output_finale['siret_final'].append(siret_final)
                output_finale['x_rp'].append( X_RP)
                output_finale['y_rp'].append( Y_RP)
                output_finale['sourcexyw_rp'].append(SourceXYW)
                output_finale['qualxy_rp'].append( qual)
                output_finale['rs_rp'].append( raison_sociale_declaree)
                position +=1
                print(output_finale)
                     
    i+=1
    print(i)

#Tous les 100 etablissements on écrit tout dans un fichier
    if i % 100 == 0:       
        df = pd.DataFrame(data=output_finale)

        
        df.to_csv('D:/S4LWO8/Mes Documents/hackathon/output files/api_qwant'+str(i)+'.csv', ";")
        
        #on réinitialise pour libérer de la mémoire
        output_finale = {'cabbi' : []
        , 'siret': []
        , 'siret_final' : []
        , 'is_equals' : []
        , 'position_page' : []
        , 'x_rp': []
        , 'y_rp': []
        , 'sourcexyw_rp': []
        , 'qualxy_rp': []
        , 'rs_rp' : []}
        

    
   
#Si on a encore des choses en mémoire à la fin on écrit un dernier fichier     
if len(output_finale['cabbi']) != 0 :
    df = pd.DataFrame(data=output_finale)
    
    print (output_finale)
    df.to_csv('D:/S4LWO8/Mes Documents/hackathon/output files/api_qwant'+str(i)+'etab_final.csv', ";")
    
            
            
#!/usr/bin/env python
# coding: utf-8

# # Web Scraping - Instagram Ray

# ### Librerías

# In[25]:



#Importamos las librerías
from selenium import webdriver
import time
import os
import time
import requests
from pprint import pprint
from bs4 import BeautifulSoup
import pandas as pd

import json
from lxml import html
import re
import csv
import numpy as np

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    )

from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
import matplotlib.pyplot as plt


# In[23]:


#Declaramos los tiempos - Scraping

WAIT_TIME   = 10
WAIT_TIME_2 = 5
WAIT_TIME_3 = 3
WAIT_TIME_4 = 0.5
WAIT_TIME_5 = 1

chromedriver_path = 'Mi_ruta/chromedriver'


# Ingremamos nuestras credenciales

# In[24]:



CONTRASENA = 'Contraseña-Instagram'
USUARIO = 'Usuario-Instagram'


# ### Funciones

# In[26]:



#Ejecutamos Chrome y definimos el link de instagram con Selenium
def load_instagram():
    # Chrome driver
    executable_path=os.path.join(chromedriver_path)

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-notifications')

    # 1=Allow, 2=Block y 0=default
    preferences = {
        "profile.default_content_setting_values.notifications" : 2,
        "profile.default_content_setting_values.location": 2,
        # capturamos solo las URLs.
        "profile.managed_default_content_settings.images": 1,
        }
    options.add_experimental_option("prefs", preferences)


    browser = webdriver.Chrome(
        executable_path=executable_path,
        chrome_options=options,
        )
    browser.wait = WebDriverWait(browser, WAIT_TIME)   
    
    #Ejecutamos el browser y url

    url = "https://www.instagram.com/"
    browser.get(url)
    
    #esperamos 5 seg para cargar
    time.sleep(WAIT_TIME_2)
       
    return browser


#Iniciamos sesión con nuestro usuario y contraseña definido previamente
def instagram_login(driver):
    usr = driver.find_element_by_name("username")
    usr.send_keys(USUARIO)
    password = driver.find_element_by_name("password")
    password.send_keys(CONTRASENA)
    password.send_keys(Keys.RETURN)
    time.sleep(WAIT_TIME_2)
    

#Obtenemos toda la información del Post por Tag    
def get_info_by_tag(keyword,browser,max_number_images):

    print(f"Scraping all the info. It will take at around {WAIT_TIME_5*max_number_images} seconds")
    
    searchbox = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search']")))
    searchbox.clear()
    # Search by tag
    searchbox.send_keys(keyword)
    time.sleep(WAIT_TIME_3)
    searchbox.send_keys(Keys.ENTER)
    time.sleep(WAIT_TIME_3)
    searchbox.send_keys(Keys.ENTER)
    time.sleep(WAIT_TIME_3)
    
    
    image_urls = []
    likes_lst  = []
    comments_lst = []
    img_urls_err =[]
    user_name_lst =[]
    post_date_lst =[]
    post_id_lst =[]
    
    image_count = 0
    first_time  = True
    while image_count < max_number_images:
        #scroll to end
        scroll_to_end(browser)
        
        # Obtenemos los atributos src attributes de las imagenes
        images    = fetch_images(browser,first_time)
        firs_time = False
        
        # Fecha, comentarios, likes, usuarios, usuario, post id, link de las imagenes de cada posts
        likes_comments = fetch_likes_comments(browser,image_urls)
            
        likes    = likes_comments[1]
        comments = likes_comments[0]
        img_err  = likes_comments[2]
        names  = likes_comments[3]
        post_date  = likes_comments[4]
        post_id  = likes_comments[5]
        
        
        # Lo asignamos
        comments_lst += comments
        likes_lst    += likes
        img_urls_err += img_err
        image_urls   += images
        user_name_lst += names
        post_date_lst += post_date
        post_id_lst += post_id
        
        image_count = len(image_urls)
        
        # Si el número de images > max número de images
        if image_count >= max_number_images:
            print(f"Found: {image_count} image links, done!")
            break
     
        
    print('Number of scraped images: ', len(likes_lst))
    
    return {'User': names,'Image URL':image_urls[:len(likes_lst)],'Likes':likes_lst,'Comments':comments_lst,'Date':post_date_lst,'Id_post':post_id_lst}    

#Scrolldown de la ventana
def scroll_to_end(driver):

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(WAIT_TIME_4)
    

#localhost de las imagenes (desde una Url)
def persist_image(folder_path:str,url:str, counter,image_name_lst):

    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        img_name =  'jpg' + "_" + str(counter) + ".jpg"
        f = open(os.path.join(folder_path,img_name), 'wb')
        f.write(image_content)
        f.close()
        print(f"SUCCESS - saved {url} - as {folder_path}")
        image_name_lst.append(img_name)
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

#Función para la busqueda de los links de cada imagen por Post        
def fetch_images(browser, first_time=True):

    #seleccionamos las imagenes
    images = browser.find_elements_by_tag_name('img')
    images = [image.get_attribute('src') for image in images]
    
    if first_time:
        images = images[1:-2] #slicing-off
    else:    
        images = images[:-2] #slicing-off IG logo
    
    return images        
        
#Función para la busqueda de los comentarios, likes, usuario, Id y Fecha por Post         
def fetch_likes_comments(browser,images):
    
    likes_lst   = []
    comment_lst = []
    user_name_lst = []
    post_date_lst = []
    post_id_lst = []
    imag_error  = []
    counter = 0
    for image in images:
        try: 
            # Click y abrimos cada Post
            browser.execute_script("arguments[0].click();",
                                   browser.find_element_by_xpath('//img[@src="'+str(image)+'"]'))
            time.sleep(WAIT_TIME_5)
            
            # Búsqueda de cada comentario, post por cada Post clicked
            likes_lst   = fetch_likes(browser,likes_lst)  
            comment_lst = fetch_comments(browser,comment_lst)
            user_name_lst = fetch_user_name(browser,user_name_lst)
            post_date_lst = fetch_post_date(browser,post_date_lst)
            post_id_lst = fetch_post_id(browser,post_id_lst)
        except Exception as e:
            print(f"ERROR - Could not fetch information from image {image} ---error: {e}")                                  
            imag_error.append(image)
            likes_lst   = ['Error']
            comment_lst = ['Error']
            
    return [comment_lst,likes_lst,imag_error,user_name_lst,post_date_lst,post_id_lst]


#Función para obtener los likes de cada Post         
def fetch_likes(browser,likes_lst):

    el_likes = "None"
    try:
        el_likes = browser.find_element_by_css_selector(".Nm9Fw > * > span").text
                      
    except Exception as e:
        try:
            el_likes = browser.find_element_by_css_selector(".Nm9Fw > button").text
        
        except Exception as e2:
            try:
                el_likes = browser.find_element_by_css_selector(".vcOH2").text
            except Exception as e3:
                print(f"ERROR - Could not fetch like  {e3}")  
    
    # Si no hay likes en las públicaciones
    if el_likes == "indicar que te gusta esto":
        el_likes = '0'
        
    # Limpiar la información   
    if "Me gusta" in str(el_likes) or "reprodu" in str(el_likes):
        el_likes = el_likes[:1]
        
        
    likes_lst.append(el_likes)
    return likes_lst

#Función para obtener los comentarios de cada post
def fetch_comments(browser,comment_lst):

    comment = [["None"]]
    try:
        comment_elements = browser.find_elements_by_css_selector(".eo2As .gElp9 .C4VMK")
        comment = [element.find_elements_by_tag_name('span')[1].text for element in comment_elements]
      
    except Exception as e:  
        print(f"ERROR - Could not fetch comment  {e}") 
        
    comment_lst.append(comment)   
    return comment_lst


#Función para obtener los usuarios por Post
def fetch_user_name(browser,user_name_lst):

    u_name = [["None"]]
    try:
        u_name = browser.find_elements_by_css_selector(".ZIAjV")[0].text
      
    except Exception as e:  
        print(f"ERROR - Could not fetch comment  {e}") 
        
    user_name_lst.append(u_name)   
    return user_name_lst


#Función para obtener la fecha de cada Post
def fetch_post_date(browser,post_date_lst):

    post_date = [["None"]]
    try:
        post_date = browser.find_elements_by_css_selector('time')[0].get_attribute('datetime')
      
    except Exception as e:  
        print(f"ERROR - Could not fetch comment  {e}") 
        
    post_date_lst.append(post_date)   
    return post_date_lst


#Función para obtener el Id de cada Post
def fetch_post_id(browser,post_id_lst):

    post_id = [["None"]]
    try:
        post_id = browser.current_url.split("/")[-2]
      
    except Exception as e:  
        print(f"ERROR - Could not fetch comment  {e}") 
        
    post_id_lst.append(post_id)   
    return post_id_lst

#Función para procesar la información del titulo, comentarios y Hashtag de un solo campo de nuestro DataFrame
def process_info(insta_info):
    
    df = pd.DataFrame(insta_info)
    
    # El primer comentario es considerado como Título
    df["Post"]    = df["Comments"] 
    df["Title"]    = [i[0:1] for i in list(df["Comments"])] 
    df["Comments"] = [i[1:] for i in list(df["Comments"])]
    
    # Obtenemos todo los hashtags del título
    df["Principal Hashtags"] = [ re.findall("#(\w+)", str(title))  for title in list(df["Title"])]
    
    return df


   


# ### Estructurar nuestro DataFrame

# In[27]:



#Iniciamos con los procesos del scraping 
def scrapping_instagram(keyword,max_number_images = 100,download=False):
    
    browser = load_instagram()
    instagram_login(browser)
    insta_info = get_info_by_tag(keyword,browser,max_number_images)
    browser.close()

    # Procesamos la información en un DataFrame
    df = process_info(insta_info)
    
    return  df
      


# Estructuramos nuestro DataFrame final, además de ordenarlo por números de likes:

# In[28]:



def dataframe_instagram(data_scrapping):
    
    df=data_scrapping
    df["likes_int"]=df["Likes"].replace('None','0').replace('like this','1').str.replace('view','').str.replace(',', '')
    df["likes_int"]=df["likes_int"].str.replace('s','')
    df["likes_int"]=df["likes_int"].astype(int)
    df=df.sort_values(by=['likes_int'],ascending=False)
    df=df.reindex(columns=['Date','User','Post','Principal Hashtags','Likes','Comments','Id_post','Image URL','Title','likes_int'])
    dframe_instagram=df
    dframe_instagram=dframe_instagram.reset_index(drop=True)
    
    #Habilitamos esta línea siempre y cuando tenemos que descargar los datos
    #dframe_instagram.to_csv('datascience.csv',index=False, header=True)

    return  dframe_instagram 


# ### Ingresamos el #Hashtag que deseamos buscar
# En este proceso asignamos la palabra(s) que deseamos buscar, almancear y visualizar

# In[29]:



buscar_hashtag='#datascience'

data_scrapping=scrapping_instagram(buscar_hashtag,max_number_images =50,download=False)

#DataFrame Final
data_instagram=dataframe_instagram(data_scrapping)


# ## Validamos la información de nuestro DataFrame final Instagram 🗳️

# In[30]:


data_instagram


# ## Nube de palabras ☁️  y gráfico de barras 📊 DataFrame Instagram

# ###### Nube de palabras ☁️ 

# In[31]:


#Obtenemos las palabras de todo los Post
nube_palabras = data_instagram.Post

# Declaramos y configuramos nuestra variable
cloud = WordCloud(width=400,
                      height=330,
                      max_words=150,
                      colormap='tab20c',
                      #stopwords=stopwords,
                      collocations=True).generate_from_text(str(nube_palabras))


# Utilizamos matplotlib.pyplot para mostrar nuestro wordcloud
plt.figure(figsize=(10,8))
plt.imshow(cloud)
plt.axis('off')
plt.title('TRD Instagram - Nube palabras', fontsize=13)
plt.show()


# ###### Gráfico de barras (Usuario por número de Likes) 📊 

# In[32]:


# Color
pk_colors = ['#A8B820','#705848','#7038F8','#F8D030','#EE99AC','#C03028','#F08030','#A890F0','#705898',
             '#78C850','#E0C068','#98D8D8','#A8A878','#A040A0', '#F85888','#B8A038','#B8B8D0','#6890F0']

data_instagram.plot(kind = 'bar',
             width=0.8,
             figsize=(10,4),y="likes_int",x='User',
             color = pk_colors,
             title='Usuarios Instagram VS números de Likes');


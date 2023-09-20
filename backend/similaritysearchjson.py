from flask import Flask, request
from langdetect import detect_langs
from flask_cors import CORS
import openai
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from cassandra.query import SimpleStatement
import pandas as pd 
import os
import json

cass_user = os.environ.get('cass_user')
cass_pw = os.environ.get('cass_pw')
scb_path =os.environ.get('scb_path')
open_api_key= os.environ.get('openai_api_key')
keyspace = os.environ.get('keyspace')
table_name = os.environ.get('table')
model_id = "text-embedding-ada-002"
#model_id='embed-multilingual-v2.0'
openai.api_key = open_api_key
cloud_config= {
  'secure_connect_bundle': scb_path
}

auth_provider = PlainTextAuthProvider(cass_user, cass_pw)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace(keyspace)

app = Flask(__name__)
CORS(app)

@app.route('/similaritems', methods=['POST'])
def ann_similarity_search():
    #customer_query='สีที่ดีที่ละลายได้อย่างสวยงาม'
    customer_query = request.json.get('newQuestion')
    #english_customer_text= translator.translate(customer_query)
    #print(english_customer_text.text)
    langs = detect_langs(customer_query)
    language = langs[0].lang
    print(language)
    
    customer_text = []
    customer_text.append(customer_query)
    #response = co.embed(texts=customer_text, model=model_id)

    message_objects = []
    message_objects.append({"role":"system",
                            "content":"You are a fine-tuned model trained to extract structured eCommerce product information. Extract brand, category, price and specification .Provide information back in JSON format."})

    message_objects.append({"role":"user",
                            "content": customer_query})

    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=message_objects
    )

    brand_category = completion.choices[0].message['content']

    filter_keyword=json.loads(brand_category)
    brand = str(filter_keyword['brand'].upper())
    print(brand)

    embeddings = openai.Embedding.create(input=customer_query, model=model_id)['data'][0]['embedding']
   # embeddings = response.embeddings[0]
    column = "openai_description_embedding_en"
    query = SimpleStatement(
        f"""
        SELECT product_id, brand,saleprice,product_categories, product_name_en, short_description_en, long_description_en
        FROM {keyspace}.products_cg_hybrid
        ORDER BY {column} ANN OF {embeddings}
        LIMIT 10 """
        )

    if brand != "" and brand != "null" and brand != "None" and brand != "Unknown" and brand != "N/A" and brand != "Not specified":
        query = SimpleStatement(
            f"""
            SELECT product_id,brand,saleprice,product_categories, product_name_en, short_description_en, long_description_en
            FROM {keyspace}.products_cg_hybrid
            WHERE product_name : ' + {brand} + '
            ORDER BY {column} ANN OF {embeddings}
            LIMIT 10 """
            )


    if language == "th":
        column = "openai_description_embedding_th"
        query = SimpleStatement(
            f"""
            SELECT product_id, brand,saleprice,product_categories, product_name, short_description, long_description
            FROM {keyspace}.products_cg_hybrid
            ORDER BY {column} ANN OF {embeddings}
            LIMIT 10 """
            )
        
        if brand != "" and brand != "null" and brand != "None" and brand != "Unknown" and brand != "N/A" and brand != "Not specified":
            query = SimpleStatement(
                f"""
                SELECT product_id,brand,saleprice,product_categories, product_name, short_description, long_description
                FROM {keyspace}.products_cg_hybrid
                WHERE product_name : ' + {brand} + '
                ORDER BY {column} ANN OF {embeddings}
                LIMIT 10 """
                )
    print(query)
    results = session.execute(query)
    top_products = results._current_rows
    print(len(top_products))

    if len(top_products) == 0:
        if language == "th": 
            query = SimpleStatement(
                f"""
                SELECT product_id, brand,saleprice,product_categories, product_name, short_description, long_description
                FROM {keyspace}.products_cg_hybrid
                ORDER BY {column} ANN OF {embeddings}
                LIMIT 10 """
                )
        else:
            query = SimpleStatement(
                f"""
                SELECT product_id, brand,saleprice,product_categories, product_name_en, short_description_en, long_description_en
                FROM {keyspace}.products_cg_hybrid
                ORDER BY {column} ANN OF {embeddings}
                LIMIT 10 """
                )

        results = session.execute(query)
        top_products = results._current_rows

    response = []
    for r in top_products:
        if language == "th":
            response.append({
                'id': r.product_id,
                'name': r.brand,
                'productname': r.product_name,
                'shortdescription': r.short_description,
                'longdescription': r.long_description,
                'price': r.saleprice,
                'category': r.product_categories
            })
        else:
            response.append({
                'id': r.product_id,
                'name': r.brand,
                'productname': r.product_name_en,
                'shortdescription': r.short_description_en,
                'longdescription': r.long_description_en,
                'price': r.saleprice,
                'category': r.product_categories
            })
    print(response)

    values = dict()
    values['products'] = response
    #values['botresponse'] = human_readable_response

    return values

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
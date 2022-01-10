import re
import requests
import pandas as pd
import pickle
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, log_loss

def shopeeScraper (url):
    url = url
    r = re.search(r'i\.(\d+)\.(\d+)', url)
    shop_id, item_id = r[1], r[2]
    ratings_url = 'https://shopee.co.id/api/v2/item/get_ratings?filter=0&flag=1&itemid={item_id}&limit=20&offset={offset}&shopid={shop_id}&type=0'
    data_scrape = []

    offset = 0
    print('Scraping Process...')
    while True:    
        data = requests.get(ratings_url.format(shop_id=shop_id, item_id=item_id, offset=offset)).json()

        i = 1
        try :
            for i, rating in enumerate(data['data']['ratings'], 1):
                if rating['comment'] == '':
                    pass
                else:
                    data_scrape.append([rating['rating_star'], rating['comment']])
        except :
            pass

        if i % 20:
            break

        offset += 20
    print('Scraping Done.')
    df = pd.DataFrame(data_scrape, columns=['rating', 'reviews'])
    df = df.dropna(axis=0)
    return df

def trainingData(X, y):
    #membangun vector space model/pembobotan dengan tfidf
    vectorizer = TfidfVectorizer(ngram_range=(1,4), min_df=10)
    features = vectorizer.fit_transform(X)

    #melakukan split data training untuk mengetahui akurasi
    X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=0.1, random_state=4)

    #modeling sentiment
    LR_ = LogisticRegression(C=3, solver='liblinear', max_iter=150).fit(X_train, y_train)

    #melakukan evaluasi
    # yhat = LR_.predict(X_test)
    # print('F1 score : ', f1_score(y_test, yhat, average='weighted'))

    # yhat_prob = LR_.predict_proba(X_test)
    # print ('Log Loss : ', log_loss(y_test, yhat_prob))
    
    return LR_, vectorizer

def importDataModel(path):
    df_model = pd.read_csv(path)
    df_model = df_model.dropna(axis=0)
    return df_model

def splitFeatures(df_model): 
    X = df_model['reviews']
    y = df_model['label']
    return X, y

def makeModel(X, y):
    model, vectorizer = trainingData(X, y)
    return model, vectorizer

def makeDataset(url):
    URL = url
    df = shopeeScraper(URL)
    return df

def predictData(df, model, vectorizer):
    features = vectorizer.transform(df.reviews)
    result = model.predict(features)
    df['label'] = result
    return df

def countLabel(df):
    label_positive = Counter(df.label)[1]
    label_negative = Counter(df.label)[0]
    total_label = label_positive + label_negative
    print('Persentase Label Positive : ', (label_positive/total_label)*100)
    print('Persentase Label Negative : ', (label_negative/total_label)*100)
    return label_positive, label_negative

def filterNegativeLabel(df):
    df_negative = df[df['label'] == 0]
    return df_negative

def cosineSimilarity(df_negative, vectorizer):
    X = df_negative['reviews']
    tfidf_matrix = vectorizer.transform(X)
    cos_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    return cos_sim

def recommenderSystem(cos_sim, df_negative):
    matrix = pd.DataFrame(cos_sim)
    similarity = []

    for i in range (len(matrix)):
        similarity.append(matrix[i].mean())
    df_negative['similarity'] = similarity
    df_negative = df_negative.sort_values(by='similarity', ascending=False)
    df_negative = df_negative.reset_index(drop=True)
    
    recommend = []
    print('Ulasan Negatif yang perlu diperbaiki :')
    for i in range(4):
        recommend.append(df_negative.reviews[i])
        print('{}.) {}'.format(i+1, df_negative.reviews[i]))
    return recommend

def runApp(path, df):
    PATH_DF_MODEL = path
    df_model = importDataModel(PATH_DF_MODEL)
    X, y = splitFeatures(df_model)
    model, vectorizer = makeModel(X, y)
    df = predictData(df, model, vectorizer)
    pos, neg = countLabel(df)
    df_negative = filterNegativeLabel(df)
    cos_sim = cosineSimilarity(df_negative, vectorizer)
    recommend = recommenderSystem(cos_sim, df_negative)
    print(recommend)
    return pos, neg, recommend
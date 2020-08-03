from stemming.porter2 import stem
import numpy as np
from flask import Flask, request, make_response, send_file
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from io import BytesIO
import time
import zipfile

app = Flask(__name__)

def cleanse_text(text):
    if text:
        clean = ' '.join(text.split())
        red_text = [stem(word) for word in clean.split()]
        return ' '.join(red_text)
    else:
        return text
@app.route('/cluster', methods=['POST'])
def cluster():
    data = pd.read_csv(request.files['dataset'])
    
    unstructure = 'text'
    if 'col' in request.args:
        unstructure = request.args.get('col')
    no_of_clusters = 2
    if 'no_of_clusters' in request.args:
        no_of_clusters = int(request.args.get('no_of_clusters'))
    
    data = data.fillna('NULL')
    
    data['clean_sum'] = data[unstructure].apply(cleanse_text)
    
    vectorizer = CountVectorizer(analyzer='word',
                                 stop_words='english')
    counts = vectorizer.fit_transform(data['clean_sum'])
    
    kmeans = KMeans(n_clusters=no_of_clusters)
    
    data['cluster_num'] = kmeans.fit_predict(counts)
    data = data.drop(['clean_sum'], axis=1)
    
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, sheet_name='Clusters', 
                  encoding='urf-8', index=False)
    
    clusters = []
    for i in range(np.shape(kmeans.cluster_centers_)[0]):
        data_cluster = pd.concat([pd.Series(vectorizer.get_feature_names()),
                                  pd.DataFrame(kmeans.cluster_centers_[i])], axis=1)
        data_cluster.columns = ['keywords', 'weights']
        data_cluster = data_cluster.sort_values(by=['weights'], ascending=False)
        data_clust = data_cluster.head(n=10)['keywords'].tolist()
        clusters.append(data_clust)
    pd.DataFrame(clusters).to_excel(writer, sheet_name='Top_Keywords', encoding='utf-8')
    # Pivot
    data_pivot = data.groupby(['cluster_num'], as_index=False).size()
    data_pivot.name = 'size'
    data_pivot = data_pivot.reset_index()
    data_pivot.to_excel(writer, sheet_name='Cluster_Report',
                  encoding='utf-8', index=False)        
    
    
    writer.save()
    
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        names = ['cluster_output.xlsx']
        files = [output]
        for i in range(len(files)):
            data = zipfile.ZipInfo(names[i])
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, files[i].getvalue())
    memory_file.seek(0)
    response = make_response(send_file(memory_file, attachment_filename='cluster_output.zip',
                                       as_attachment=True))
    response.headers['Content-Disposition'] = 'attachment;filename=cluster_output.zip'
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response
                     
    
if __name__=='__main__':
    app.run(host='0.0.0.0')

        
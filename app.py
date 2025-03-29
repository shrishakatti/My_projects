from flask import Flask, render_template, request
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import mysql.connector

app = Flask(__name__)

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="PAML"
)
cursor = mydb.cursor()



model = joblib.load('C:/Users/abhin/OneDrive/Documents/PAML/model.joblib')


def preprocess_data(df):
    
    tokenizer_org = tf.keras.preprocessing.text.Tokenizer()
    tokenizer_org.fit_on_texts(df['nameOrig'])

    tokenizer_dest = tf.keras.preprocessing.text.Tokenizer()
    tokenizer_dest.fit_on_texts(df['nameDest'])

    
    customers_train_org = tokenizer_org.texts_to_sequences(df['nameOrig'])
    customers_test_org = tokenizer_org.texts_to_sequences(df['nameOrig'])

    customers_train_dest = tokenizer_dest.texts_to_sequences(df['nameDest'])
    customers_test_dest = tokenizer_dest.texts_to_sequences(df['nameDest'])

    df['customers_org'] = tf.keras.preprocessing.sequence.pad_sequences(customers_train_org, maxlen=1)
    df['customers_org'] = tf.keras.preprocessing.sequence.pad_sequences(customers_test_org, maxlen=1)

    df['customers_dest'] = tf.keras.preprocessing.sequence.pad_sequences(customers_train_dest, maxlen=1)
    df['customers_dest'] = tf.keras.preprocessing.sequence.pad_sequences(customers_test_dest, maxlen=1)

  
    col_names = ['amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest']
    scaler = StandardScaler().fit(df[col_names].values)
    df[col_names] = scaler.transform(df[col_names].values)

    
    df['orig_txn_diff'] = df['amount'] - (df['newbalanceOrig'] - df['oldbalanceOrg'])
    df['dest_txn_diff'] = df['amount'] - (df['newbalanceDest'] - df['oldbalanceDest'])
    df['orig_diff'] = np.where(df['orig_txn_diff'] != 0, 1, 0)
    df['dest_diff'] = np.where(df['dest_txn_diff'] != 0, 1, 0)

  
    df['surge'] = np.where(df['amount'] > 450000, 1, 0)

   
    freq_dest_counts = df['nameDest'].value_counts()
    df['freq_dest'] = df['nameDest'].map(freq_dest_counts)
    df['freq_dest'] = np.where(df['freq_dest'] > 20, 1, 0)

    df.drop(['nameDest', 'nameOrig'], axis=1, inplace=True)  # Drop unnecessary columns
    df.drop(['orig_txn_diff', 'dest_txn_diff'], axis=1, inplace=True)

    return df

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/predict', methods=['POST'])
def predict():
   
    step = int(request.form['step'])
    type__CASH_IN = int(request.form['type_CASH_IN'] == 'True')
    type__CASH_OUT = int(request.form['type_CASH_OUT'] == 'True')
    type__DEBIT = int(request.form['type_DEBIT'] == 'True')
    type__PAYMENT = int(request.form['type_PAYMENT'] == 'True')
    type__TRANSFER = int(request.form['type_TRANSFER'] == 'True')
    amount = float(request.form['amount'])
    nameOrig = request.form['nameOrig']
    oldbalanceOrg = float(request.form['oldbalanceOrg'])
    newbalanceOrig = float(request.form['newbalanceOrig'])
    nameDest = request.form['nameDest']
    oldbalanceDest = float(request.form['oldbalanceDest'])
    newbalanceDest = float(request.form['newbalanceDest'])

    
    dummy_size = 1  
    orig_diff = np.zeros(dummy_size)
    dest_diff = np.zeros(dummy_size)
    surge = np.zeros(dummy_size)
    freq_dest = np.zeros(dummy_size)
    customers_org = np.zeros(dummy_size)
    customers_dest = np.zeros(dummy_size)

   
    user_data = pd.DataFrame({
        'step': [step],
        'amount': [amount],
        'oldbalanceOrg': [oldbalanceOrg],
        'newbalanceOrig': [newbalanceOrig],
        'oldbalanceDest': [oldbalanceDest],
        'newbalanceDest': [newbalanceDest],
        'orig_diff': orig_diff,
        'dest_diff': dest_diff,
        'surge': surge,
        'freq_dest': freq_dest,
        'type__CASH_IN': [type__CASH_IN],
        'type__CASH_OUT': [type__CASH_OUT],
        'type__DEBIT': [type__DEBIT],
        'type__PAYMENT': [type__PAYMENT],
        'type__TRANSFER': [type__TRANSFER],
        'customers_org': customers_org,
        'customers_dest': customers_dest,
        'nameOrig': [nameOrig],
        'nameDest': [nameDest],
    })

   
    user_data = preprocess_data(user_data)

    
    prediction = model.predict(user_data)
    orig_diff = orig_diff[0]
    dest_diff = dest_diff[0]
    surge = surge[0]
    freq_dest = freq_dest[0]
    customers_org = customers_org[0]
    customers_dest = customers_dest[0]

    
    query = "INSERT INTO transactions (step, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, orig_diff, dest_diff, surge, freq_dest, type__CASH_IN, type__CASH_OUT, type__DEBIT, type__PAYMENT, type__TRANSFER, customers_org, customers_dest) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (step, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest, orig_diff, dest_diff, surge, freq_dest, type__CASH_IN, type__CASH_OUT, type__DEBIT, type__PAYMENT, type__TRANSFER, customers_org, customers_dest)

    cursor.execute(query, values)
    mydb.commit()

    return render_template('classification_result.html', prediction=prediction[0])

@app.route('/view_data', methods=['GET', 'POST'])
def view_data():
    if request.method == 'POST':
       
        cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        data = cursor.fetchall()

        return render_template('view_data.html', data=data)
    else:
        cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        data = cursor.fetchall()
        return render_template('view_data.html')

if __name__ == '__main__':
    app.run(debug=True)

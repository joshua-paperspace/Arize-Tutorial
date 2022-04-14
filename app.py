from this import d
from flask import Flask, request, Response, render_template, redirect, url_for
import pandas as pd
import xgboost as xgb
from arize.pandas.logger import Client, Schema
from arize.utils.types import Environments, ModelTypes

# MODEL_PATH = '/opt/models/xgb_model.json'
MODEL_PATH = './xgb_cl_model.json'

app = Flask(__name__)

@app.route('/')
def health_check():
    return 'Healthy!'
    

@app.route('/prediction', methods=['POST'])
def churn_prediction():

    request_data = request.get_json()
    df = pd.DataFrame([request_data])

    # Preprocessing
    target = ['Churn']
    categorical_cols = ['gender', 'SeniorCitizen', 'Partner', 'Dependents',
        'PhoneService', 'MultipleLines', 'InternetService',
        'OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport',
        'StreamingTV', 'StreamingMovies', 'Contract', 'PaperlessBilling',
        'PaymentMethod']
    continuous_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']

    # df.drop(df[df['TotalCharges'].str.strip() == ''].index, inplace=True)
    # df.reset_index(inplace=True, drop=True)
    orig = df.copy()

    
    df = pd.get_dummies(df.drop(['customerID'], axis=1), columns=categorical_cols)
    # df = pd.get_dummies(df, columns = target)
    # df.rename(columns={'Churn_Yes': 'Churn'}, inplace=True)

    def min_max_normalize(col):
        return col / col.abs().max()

    for col in continuous_cols:
        df[col] = df[col].astype('float64')
        df[col] = min_max_normalize(df[col])

    all_cols = ['tenure', 'MonthlyCharges', 'TotalCharges', 'gender_Female',
       'gender_Male', 'SeniorCitizen_0', 'SeniorCitizen_1', 'Partner_No',
       'Partner_Yes', 'Dependents_No', 'Dependents_Yes', 'PhoneService_No',
       'PhoneService_Yes', 'MultipleLines_No',
       'MultipleLines_No phone service', 'MultipleLines_Yes',
       'InternetService_DSL', 'InternetService_Fiber optic',
       'InternetService_No', 'OnlineSecurity_No',
       'OnlineSecurity_No internet service', 'OnlineSecurity_Yes',
       'OnlineBackup_No', 'OnlineBackup_No internet service',
       'OnlineBackup_Yes', 'DeviceProtection_No',
       'DeviceProtection_No internet service', 'DeviceProtection_Yes',
       'TechSupport_No', 'TechSupport_No internet service', 'TechSupport_Yes',
       'StreamingTV_No', 'StreamingTV_No internet service', 'StreamingTV_Yes',
       'StreamingMovies_No', 'StreamingMovies_No internet service',
       'StreamingMovies_Yes', 'Contract_Month-to-month', 'Contract_One year',
       'Contract_Two year', 'PaperlessBilling_No', 'PaperlessBilling_Yes',
       'PaymentMethod_Bank transfer (automatic)',
       'PaymentMethod_Credit card (automatic)',
       'PaymentMethod_Electronic check', 'PaymentMethod_Mailed check']

    df = df.reindex(df.columns.union(all_cols, sort=False), axis=1, fill_value=0)
    print(df.columns)
    # df2 = df[all_cols]
    # df2 = df.drop(categorical_cols, axis=1, errors='ignore')

    print('here')
    print(df.shape)
    print(df.columns)

    #XGBoost Classifier
    xgb_cl = xgb.XGBClassifier()
    xgb_cl.load_model(MODEL_PATH)

    # print('here')
    # print(df.shape)
    # print(df.columns)
    pred = xgb_cl.predict(df)
    # print(accuracy_score(y_test, preds2))

    print(pred)



    SPACE_KEY = "be431ff"
    API_KEY = "3b6a922ea5ac74536e7"

    arize_client = Client(space_key=SPACE_KEY, api_key=API_KEY)

    model_id = (
        "telco-churn-demo-model"  # This is the model name that will show up in Arize
    )
    model_version = "v1.0"  # Version of model - can be any string

    if SPACE_KEY == "SPACE_KEY" or API_KEY == "API_KEY":
        raise ValueError("❌ NEED TO CHANGE SPACE AND/OR API_KEY")
    else:
        print("✅ Arize setup complete!")


    print('HEREERHERHERH')
    print(orig.columns)
    # return
    single_pred = orig.copy()
    single_pred['Predicted_Churn'] = pred[0]
    # single_pred  = pd.concat([orig, pd.DataFrame(pred, columns=['Prediction'])], axis=1)


    feature_cols = single_pred.drop(['customerID', 'Predicted_Churn'], axis=1).columns
    ## Test a single Prod prediction

    # Define a Schema() object for Arize to pick up data from the correct columns for logging
    ## Add Dates in here somewhere!
    prod_schema = Schema(
        prediction_id_column_name="customerID",
        prediction_label_column_name="Predicted_Churn",
        # actual_label_column_name="Churn",
        feature_column_names=feature_cols,
    )

    # Logging Prod DataFrame
    prod_response = arize_client.log(
        dataframe=single_pred,
        model_id=model_id,
        model_version=model_version,
        model_type=ModelTypes.SCORE_CATEGORICAL,
        environment=Environments.PRODUCTION,
        schema=prod_schema,
    )

    # If successful, the server will return a status_code of 200
    if prod_response.status_code != 200:
        print(
            f"logging failed with response code {prod_response.status_code}, {prod_response.text}"
        )
    else:
        print(f"✅ You have successfully logged production data to Arize")


    return Response(pred[0], status=201, content_type='application/json')

    df = pd.read_json(request_data)

    print(df)

    # language = request_data['language']
    # framework = request_data['framework']



    # image = Image.open(request.form['img'])

    # image_functionality(prompt)

    # filename = 'static/uploads/uploaded_image.png'
    # image.save(filename)

    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # model = resnet18(3, 10)
    # model.load_state_dict(torch.load(MODEL_PATH, map_location=device))

    # tensor = imgToTensor(image)
    
    # output = model(tensor)
    # _, predicted = torch.max(output.data, 1)
    # print(predicted)
    # prediction = classes[predicted]

    # return render_template('result.html', prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8000')

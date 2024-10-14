import base64
from cgi import FieldStorage
import io
import json
from typing import Dict, Tuple

import pandas as pd

try:
    # serverless offlineを使う場合は実行パスの違いでimportできないため
    from api.src.problem import CarGroupProblem
except ModuleNotFoundError:
    from src.problem import CarGroupProblem


def preprocess(event) -> Tuple[pd.DataFrame, pd.DataFrame]:
    fp = io.BytesIO(base64.b64decode(event['body']))
    environ = {'REQUEST_METHOD': 'POST'}
    headers = {
        'content-type': event['headers']['Content-Type'],
        'content-length': event['headers']['Content-Length']
    }

    fs = FieldStorage(fp=fp, environ=environ, headers=headers)

    dfs: Dict[str, pd.DataFrame] = {}
    for f in fs.list:
        if f.name == 'students':
            dfs['students'] = pd.read_csv(io.BytesIO(f.value))
        if f.name == 'cars':
            dfs['cars'] = pd.read_csv(io.BytesIO(f.value))

    return dfs['students'], dfs['cars']


def postprocess(solution_df):
    """データフレームを csv に変換する関数"""
    ret = solution_df.to_json()
    response = {
        'headers': {'Content-Type': ''},
        'body': {'message': '', 'data': ''}
    }
    response['statusCode'] = 200
    response['headers']['Content-Type'] = 'text/csv'
    response['body']['message'] = 'OK'
    response['body']['data'] = ret

    response['body'] = json.dumps(response['body'])

    return response


def hello(event, context):
    students, cars = preprocess(event)
    solution: pd.DataFrame = CarGroupProblem(students, cars).solve()
    response = postprocess(solution)

    return response

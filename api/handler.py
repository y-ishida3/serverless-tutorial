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
    # :TODO csvのcolumnに文字化けが発生するので、解消する必要がある
    buffer = io.BytesIO()
    solution_df.to_csv(buffer, index=False, encoding='utf-8', sep=',')
    body = base64.b64encode(buffer.getvalue()).decode('utf-8')

    response = {}
    response['statusCode'] = 200
    response['isBase64Encoded'] = True
    response['headers'] = {
        'Content-Type': 'text/csv',
        'Content-disposition': 'attachment; filename=hoge.csv'
    }
    response['body'] = json.dumps({
        'data': body
    })

    return response


def solve(event, context):
    students, cars = preprocess(event)
    solution: pd.DataFrame = CarGroupProblem(students, cars).solve()
    response = postprocess(solution)

    return response

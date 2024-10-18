import base64
from cgi import parse_multipart, parse_header
import io
from typing import Dict, Tuple

import pandas as pd

try:
    # serverless offlineを使う場合は実行パスの違いでimportできないため
    from api.src.problem import CarGroupProblem
except ModuleNotFoundError:
    from src.problem import CarGroupProblem


def preprocess(event) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # cf. https://tmyoda.hatenablog.com/entry/20210304/1614800890
    if event['headers'].get('content-type'):
        c_type, c_data = parse_header(event['headers']['content-type'])
    elif event['headers'].get('Content-Type'):
        c_type, c_data = parse_header(event['headers']['Content-Type'])
    else:
        raise RuntimeError('content-type or Content-Type not found')

    # :NOTE serverless offlineでrequest投げた時とdeploy後のlambdaのrequestが違うため
    if event['isBase64Encoded']:
        # base64でencodeされている場合は、base64でdecodeしてbyte型に
        body: bytes = base64.b64decode(event['body'])
    else:
        # strの場合はencodeしてbyte型に
        body: bytes = event['body'].encode(encoding='utf-8')
    # For Python 3: these two lines of bugfixing are mandatory
    # cf. https://stackoverflow.com/questions/31486618/cgi-parse-multipart-function-throws-typeerror-in-python-3
    c_data['boundary'] = bytes(c_data['boundary'], 'utf-8')
    data_dict = parse_multipart(io.BytesIO(body), c_data)

    files = {k: v[0] for k, v in data_dict.items()}

    dfs: Dict[str, pd.DataFrame] = {}
    for key, value in files.items():
        if key == 'students':
            dfs['students'] = pd.read_csv(io.BytesIO(value))
        if key == 'cars':
            dfs['cars'] = pd.read_csv(io.BytesIO(value))

    return dfs['students'], dfs['cars']


def postprocess(solution_df):
    buffer = io.StringIO()
    solution_df.to_csv(buffer, index=False, encoding='utf-8', sep=',')
    body = buffer.getvalue()

    response = {}
    response['statusCode'] = 200
    response['headers'] = {
        'Content-Type': 'text/csv',
        'Content-disposition': 'attachment; filename=test.csv'
    }
    response['body'] = body

    return response


def solve(event, context):
    students, cars = preprocess(event)
    solution: pd.DataFrame = CarGroupProblem(students, cars).solve()
    response = postprocess(solution)

    return response

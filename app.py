from WCS_dash import RollingAverage
import dash_core_components as dcc
import dash_html_components as html
import os
import csv
import pandas as pd
import numpy as np
import dash
import dash_table
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import base64
import io

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    html.Div(id='wcs-data'),
    #dcc.Graph(id='wcs-heatmap'),
])


@app.callback(
    Output('wcs-data', 'children'),
    [Input('upload-data', 'contents')])
def create_heatmap(csv_file):
    content_type, content_string = csv_file.split(',')
    decoded = base64.b64decode(content_string)
    rolling_calculator = RollingAverage(decoded)
    rolling_calculator.apply_all_calculations()

    interim = {k: pd.DataFrame(v) for k,v in rolling_calulator.results.items()}
    table = dash_table.DataTable(
        id='table',
        columns=[{"name":i, "id":i} for i in rolling_calculator.results.columns],
        data=rolling_calculator.results.to_dict('records'),
    )
    return html.Div([
        table,
        dcc.Graph(id='graph',
                 figure= rolling_calculator.plot_heatmap())
    ])

if __name__ == '__main__':
    app.run_server(debug=True)


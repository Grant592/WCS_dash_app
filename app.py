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
        multiple=True
    ),
    html.Div(id='wcs-data'),
    #dcc.Graph(id='wcs-heatmap'),
])


@app.callback(
    Output('wcs-data', 'children'),
    [Input('upload-data', 'contents')])
def create_heatmap(csv_files):
    div_list = []
    for csv_file in csv_files:
        content_type, content_string = csv_file.split(',')
        decoded = base64.b64decode(content_string)
        rolling_calculator = RollingAverage(decoded)
        rolling_calculator.apply_all_calculations()

        calculated_results = {k: pd.DataFrame(v) for k,v in rolling_calculator.results.items()}
        results_df = pd.concat(calculated_results, axis=1)
        results_df = results_df.droplevel(0, axis=1)
        results_df.reset_index(inplace=True)
        print(results_df)
        print(results_df.columns)
        if len(csv_files) > 1:
            div_list.append(html.Div(
                [
                html.Div([
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name":i, "id":i} for i in results_df.columns],
                        data=results_df.to_dict('records')
                    )
                ], style={'width':'90%', 'display': 'inline-block', 'vertical-align': 'middle', 'textalign':'center'}
                ),
                dcc.Graph(id='graph',
                     figure= rolling_calculator.plot_heatmap())
                ],
                style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'middle'}
            ))
        else:
            div_list.append(html.Div(
                [
                html.Div([
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name":i, "id":i} for i in results_df.columns],
                        data=results_df.to_dict('records')
                    )
                ], style={'width':'90%', 'display': 'inline-block', 'vertical-align': 'middle', 'textalign':'center'}
                ),
                dcc.Graph(id='graph',
                     figure= rolling_calculator.plot_heatmap())
                ],
            ))



    return html.Div([
        div for div in div_list
        ]
    )


if __name__ == '__main__':
    app.run_server(debug=True)


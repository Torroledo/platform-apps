import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ClientsideFunction
from calculating_metrics import *

import numpy as np
import pandas as pd
import datetime
from datetime import datetime as dt
import pathlib
import plotly.graph_objs as go

import pandas as pd

# ============================== SETUP ============================== #
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    __name__,
    meta_tags = [{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets = external_stylesheets
)
server = app.server
app.config.suppress_callback_exceptions = True
# ============================== DECLARATIONS ======================= #

def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


# Sample data set parameters
num_clients = 100
time_frame = '2016-01-01', '2019-01-01'
num_products = 10
num_transactions = 100
avg_sale = 1000 # USD

# RFM analysis
alpha = [0.3,0.3,0.2,0.2]

n_groups = 5
selected_columns = ['score','client_id','tenure','last_purchase','months_since_last','sales','segment']

sales_data = create_random_data_set(time_frame , num_clients, num_transactions, num_products, avg_sale)

scores_table = run_RFM_analysis(sales_data,n_groups,alpha)#.set_index('score')
lime_table = scores_table.groupby('segment').median()[['recency_value','frequency_value','monetary_value']].reset_index()

health = (scores_table.groupby('segment').sum()['monetary_value']/scores_table.monetary_value.sum()).to_frame('sales_share')
health['size'] = scores_table.segment.value_counts(normalize=True)
health.reset_index(inplace=True)

# ============================== LAYOUT ============================== #

app.layout = html.Div(
    id="app-container",
    children=[
        html.Div(id='alphas', style={'display': 'none'}),
        # Header Banner
        html.Div(
            id="banner",
            className="banner",
            children=[
                html.Img(
                    src=app.get_asset_url("platform_logo.png"),
                )
            ],
        ),
        # Options Selection Banner
        html.Div(
            children=[
                html.Div(
                    className='three columns offset-by-one',
                    id='parameters-banner',
                    children=[
                        html.H3('This is the selection banner'),
                        html.Div([
                            html.P("Recency"),
                            dcc.Input(id='alpha-r', value='0.25', type='number'),
                        ]),
                        html.Div([
                            html.P("Frequency"),
                            dcc.Input(id='alpha-f', value='0.25', type='number')
                        ]),
                        html.Div([
                            html.P("Monetary"),
                            dcc.Input(id='alpha-m', value='0.25', type='number'),
                        ]),
                        html.Div([
                            html.P("Tenure"),
                            dcc.Input(id='alpha-a', value='0.25', type='number'),
                        ])
                    ]
                ),
                # General health business Banner
                html.Div(
                    children=[
                        html.H3(children='Business Health'),
                        dcc.Graph(
                            id='example-graph',
                            figure={
                                'data': [
                                    {
                                        'x': health['segment'],
                                        'y': health['sales_share'],
                                        'type': 'bar',
                                        'name': 'Sales',
                                        'marker_color':  'blue'
                                    },
                                    {
                                        'x': health['segment'],
                                        'y': health['size'],
                                        'type': 'bar',
                                        'name': 'Size',
                                        'marker_color': 'red'
                                    },
                                ],
                                'layout': {
                                    'title': 'Revenue decomposition'
                                }
                            }
                        )
                    ],
                    className = 'seven columns offset-by-one'
                )
            ],
            id="first-row",
            className="row",
        ),
        # Detailed table banner
        html.Div(
            id="third-row",
            className="row",
            children=[
                html.H3(children='Sales Control Panel'),
                html.Div(
                    className='ten columns offset-by-one',
                    # children = generate_table(scores_table)
                    children=dash_table.DataTable(
                        data=scores_table[selected_columns].to_dict('records'),
                        columns=[{'id': c, 'name': c} for c in selected_columns],
                        fixed_rows={'headers': True, 'data': 0},
                        style_cell={
                            'minWidth': '180px',
                            'width': '180px',
                            # 'maxWidth': '180px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        },
                        style_table={
                            'maxHeight': '300px',
                            'overflowY': 'scroll',
                            'border': 'thin lightgrey solid'
                        },
                    )
                )
            ]
        ),
        # Lime plots Banner
        html.Div(
            id='lime-banner',
            children=[
                html.H3(children='RFM Analysis'),
                html.Div(
                    className='four columns',
                    id='recency-lime-sub-banner',
                    children=[
                        dcc.Graph(
                            id = 'recency-lime-bar-chart',
                            figure={
                                'data': [
                                    go.Bar(
                                        x=lime_table['recency_value'],
                                        y=lime_table['segment'],
                                        marker_color = ['tomato',] * lime_table['segment'].shape[0],
                                        orientation='h'
                                    )
                                ],
                                'layout': {
                                    'title': 'Recency'
                                }
                            }
                        )
                    ],
                ),
                html.Div(
                    className='four columns',
                    id='frequency-lime-sub-banner',
                    children=[
                        dcc.Graph(
                            id = 'frequency-lime-bar-chart',
                            figure={
                                'data': [
                                    go.Bar(
                                        x=lime_table['frequency_value'],
                                        y=lime_table['segment'],
                                        marker_color = ['blue'] * lime_table['segment'].shape[0],
                                        orientation='h'
                                    )
                                ],
                                'layout': {
                                    'title': 'Frequency'
                                }
                            }
                        )
                    ]
                ),
                html.Div(
                    className='four columns',
                    id='sales-lime-sub-banner',
                    children=[
                        dcc.Graph(
                            id = 'sales-lime-bar-chart',
                            figure={
                                'data': [
                                    go.Bar(
                                        x=lime_table['monetary_value'],
                                        y=lime_table['segment'],
                                        marker_color = ['lightslategray',] * lime_table['segment'].shape[0],
                                        orientation='h'
                                    )
                                ],
                                'layout': {
                                    'title': 'Sales'
                                }
                            }
                        )
                    ]
                )
            ]
        )
    ]
)

# @app.callback(
#     [
#         Input(component_id = "alpha-r", component_property = "value"),
#         Input(component_id = "alpha-f", component_property = "value"),
#         Input(component_id = "alpha-m", component_property = "value"),
#         Input(component_id = "alpha-a", component_property = "value"),
#     ],
# )
def update_choro(alpha_r,alpha_f,alpha_m,alpha_a):
    return [alpha_r,alpha_f,alpha_m,alpha_a]


# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)

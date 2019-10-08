import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ClientsideFunction
from calculating_metrics import *
import pickle
import pandas as pd
import plotly.graph_objs as go

import numpy as np
import datetime
from datetime import datetime as dt
import pathlib

# ============================== SETUP ============================== #
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    __name__,
    meta_tags = [{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets = external_stylesheets
)
server = app.server
app.config.suppress_callback_exceptions = True
# ============================== DB connection ======================= #


# Sample data set parameters
num_clients = 100
time_frame = '2016-01-01', '2019-01-01'
num_products = 10
num_transactions = 100
avg_sale = 1000 # USD

# RFM analysis
n_groups = 5
selected_columns = ['score','client_id','tenure','last_purchase','months_since_last','sales','segment']
sales_data = create_random_data_set(time_frame , num_clients, num_transactions, num_products, avg_sale)

# ============================== DECLARATIONS ======================= #

def save_pickle(obj,obj_name):
    with open('data/temporal/'+obj_name+'.pickle', 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)

def load_pickle(obj_name):
    with open('data/temporal/'+obj_name+'.pickle', 'rb') as handle:
        return pickle.load(handle)

# ============================== LAYOUT ============================== #

app.layout = html.Div(
    id="app-container",
    children=[
        # Header Banner
        html.Div(
            id="header",
            className="banner",
            children=[
                html.Img(
                    src=app.get_asset_url("platform_logo.png"),
                )
            ]
        ),
        # Options Selection Banner
        html.Div(
            id="first-section",
            className="row",
            children=[
                html.Div(
                    id='parameters-banner',
                    className='three columns offset-by-one',
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
                    id = 'health-section',
                    className = 'seven columns offset-by-one',
                    children=[
                        html.H3('Take your shit together'),
                        html.Div(
                            id='health-section-chart',
                            children = [
                                dcc.Graph(id='health-chart')
                            ]
                        )
                    ],
                )
            ]
        ),
        # Detailed table banner
        html.Div(
            id="second-section",
            className="row",
            children=[
                html.H3(children='Sales Control Panel'),
                html.Div(
                    id='detailed-table',
                    className='six columns offset-by-one',
                ),
                html.Div(
                    children=[
                        html.Div([
                            html.H6('Why this client is important?'),
                            dcc.Input(id='lime-filter', value='1',type='number')
                        ]
                        )
                        ,
                        html.Div(
                            id='detailed-lime-space',
                            className='three columns offset-by-one',
                            children=[
                                dcc.Graph(id='detailed-lime',
                                          figure={
        'data': [
            go.Bar(
                x=[1],#table_selection['importance'],
                y=[2],#table_selection['factor'],
                # marker_color=['lightslategray', ] * table_selection['segment'].shape[0],
                orientation='h'
            )
        ],
        'layout': {
            'title': 'client explanation'
        }
    })
                            ]
                        )
                    ],
                )
            ],

        ),
        # Lime plots Banner
        html.Div(
            id='third-section',
            className='row',
            children=[
                html.H3(children='RFM Analysis'),
                html.Div(
                    className='four columns',
                    id='recency-lime-sub-banner',
                    children=[
                        dcc.Graph(
                            id = 'recency-lime-bar-chart',
                        )
                    ],
                ),
                html.Div(
                    className='four columns',
                    id='frequency-lime-sub-banner',
                    children=[
                        dcc.Graph(
                            id = 'frequency-lime-bar-chart',
                        )
                    ]
                ),
                html.Div(
                    className='four columns',
                    id='sales-lime-sub-banner',
                    children=[
                        dcc.Graph(
                            id = 'sales-lime-bar-chart',
                        )
                    ]
                )
            ]
        )
    ]
)

# ============================== CALLBACKS ============================== #
@app.callback(
    [
        Output(component_id='health-chart', component_property='figure'),
        Output(component_id='detailed-table', component_property='children'),
        Output(component_id='recency-lime-bar-chart', component_property='figure'),
        Output(component_id='frequency-lime-bar-chart', component_property='figure'),
        Output(component_id='sales-lime-bar-chart', component_property='figure'),
    ],
    [
        Input(component_id = "alpha-r", component_property = "value"),
        Input(component_id = "alpha-f", component_property = "value"),
        Input(component_id = "alpha-m", component_property = "value"),
        Input(component_id = "alpha-a", component_property = "value"),
    ],
)
def wrap_weight_and_run_analysis(alpha_r,alpha_f,alpha_m,alpha_a):

    # retrieving alpha values
    alpha = [float(alpha_i) for alpha_i in [alpha_r,alpha_f,alpha_m,alpha_a]]
    save_pickle(alpha, 'alpha')

    # Running analysis
    scores_table = run_RFM_analysis(sales_data, n_groups, alpha)
    lime_table = scores_table.groupby('segment').median()[['recency_value', 'frequency_value', 'monetary_value']].reset_index()
    scores_table = pd.merge(scores_table, lime_table, on='segment', how='left', suffixes=('', '_segment'))
    scores_table['recency_diff'] = (scores_table['recency_value'] - scores_table['recency_value_segment'] )/ scores_table['recency_value_segment']
    scores_table['frequency_diff'] = (scores_table['frequency_value'] - scores_table['frequency_value_segment'] )/ scores_table['frequency_value_segment']
    scores_table['monetary_diff'] = (scores_table['monetary_value'] - scores_table['monetary_value_segment'] )/ scores_table['monetary_value_segment']
    save_pickle(scores_table, 'scores_table')
    save_pickle(lime_table, 'lime_table')

    # Running health assessment
    health = (scores_table.groupby('segment').sum()['monetary_value'] / scores_table.monetary_value.sum()).to_frame('sales_share')
    health['size'] = scores_table.segment.value_counts(normalize=True)
    health.reset_index(inplace=True)
    save_pickle(health, 'health')

    health_chart_out = {
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
    detailed_table_out = [
        dash_table.DataTable(
            filter_action="native",
            data=scores_table[selected_columns].to_dict('records'),
            columns=[{'id': c, 'name': c} for c in selected_columns],
            fixed_rows={'headers': True, 'data': 0},
            style_cell={
                'minWidth': '180px',
                'width': '180px',
                'maxWidth': '180px',
                # 'overflow': 'hidden',
                # 'textOverflow': 'ellipsis',
                # "padding": "15px",
                # "midWidth": "0px",
                # # "width": "25%",
                # "textAlign": "center",
                # # "border": "white",
            },
            style_table={
                'maxHeight': '300px',
                'overflowY': 'scroll',
                'border': 'thin lightgrey solid'
            },
            # style_cell_conditional = [
            #     {
            #         "if": {
            #             "row_index": "even"
            #     },
            #         "backgroundColor": "#f9f9f9"
            #     }
            # ],
            style_data={"whiteSpace": "normal"},
            # css={
            #    "rule": "display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;"
            # },
            # row_deletable=True,

        )
    ]
    recency_lime_bar_chart_out = {
        'data': [
            go.Bar(
                x=lime_table['recency_value'],
                y=lime_table['segment'],
                marker_color=['tomato', ] * lime_table['segment'].shape[0],
                orientation='h'
            )
        ],
        'layout': {
            'title': 'Recency'
        }
    }
    frequency_lime_bar_chart_out = {
        'data': [
            go.Bar(
                x=lime_table['frequency_value'],
                y=lime_table['segment'],
                marker_color=['blue'] * lime_table['segment'].shape[0],
                orientation='h'
            )
        ],
        'layout': {
            'title': 'Frequency'
        }
    }
    sales_lime_bar_chart_out = {
        'data': [
            go.Bar(
                x=lime_table['monetary_value'],
                y=lime_table['segment'],
                marker_color=['lightslategray', ] * lime_table['segment'].shape[0],
                orientation='h'
            )
        ],
        'layout': {
            'title': 'Sales'
        }
    }

    return health_chart_out,detailed_table_out,recency_lime_bar_chart_out,frequency_lime_bar_chart_out,sales_lime_bar_chart_out


@app.callback(
    [
        Output(component_id='detailed-lime', component_property='figure'),
    ],
    [
        Input(component_id="lime-filter", component_property="value"),
    ],
)
def generate_detailed_lime(identifier,):
    value_id = int(identifier)
    scores_local = load_pickle('scores_table')
    table_selection = scores_local.query('client_id == @value_id ')[[col for col in scores_local.columns if 'diff' in col]].melt(var_name='factor',value_name='importance')

    a = {'data': [go.Bar(
        x=[1],#table_selection['importance'],
        y=[2],#table_selection['factor'],
        # marker_color=['lightslategray', ] * table_selection['segment'].shape[0],
        orientation='h'
    )],
        'layout': {'title': 'client explanation'}
    }
    return a
# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)

import pandas as pd
import numpy as np
from random import randrange
from datetime import date,timedelta

def random_date(start, end):
    """
    This function returns a random datetime between two datetime
    objects
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)
def create_random_data_set(timeframe, num_clients, n, num_products, avg_sale):
    """
    create_random_data_set simulates a sample to set to play with. The function replicates
    data based on given parameters

    """
    frame_out = pd.DataFrame(index=range(0, n))
    frame_out['sales'] = np.random.rand(n, 1) * avg_sale
    frame_out['date'] = [random_date(pd.to_datetime(timeframe[0]), pd.to_datetime(timeframe[1])) for i in range(n)]
    frame_out['client_id'] = [np.random.randint(0, num_clients) for i in range(n)]
    frame_out['product_id'] = [np.random.randint(0, num_products) for i in range(n)]
    frame_out = frame_out.sort_values('date')
    return frame_out
def assign_segment(frame_in):
    """
    assign_segment performs propietary algortihm to assign a meaningful segment to each client
    according to their customer behavior

    :param
    frame_in: Pandas DataFrame object with RFM tags

    :return:
    frame_out: pandas DataFrame with client_id and assigned segment
    """

    segment_names = [name + str(i) for i, name in enumerate(['segment_'] * 9)]
    frame_out = pd.DataFrame(list(frame_in['client_id'].unique()), columns=['client_id'])
    frame_out['segment'] = np.random.choice(segment_names, len(frame_in['client_id'].unique()))
    return pd.merge(frame_in, frame_out, on='client_id')
def create_scores(frame_in, groups, weights):
    """
    create_scores creates RFM scores for sales date (frame_in)
    :param
    frame_in:   Pandas DataFrame with core client info

    :return:
    scores:
    """
    today = pd.to_datetime(date.today())
    first_date = frame_in.groupby('client_id').min()[['date']]
    last_date = frame_in.groupby('client_id').max()[['date']]

    recency = (today - last_date).apply(lambda x: int(x[0].days / 30), axis=1).to_frame(name='r')
    frequency = (today - first_date).apply(lambda x: int(x[0].days / 30), axis=1).to_frame(name='f')
    monetary = frame_in.groupby('client_id').max()['sales'].to_frame(name='m')

    scores = pd.concat([recency, frequency, monetary], axis=1).apply(
        lambda x: pd.qcut(x, q=groups, labels=[i for i in range(1, groups + 1)]).astype(int), axis=0)

    scores['group'] = scores['r'].map(str) + scores['f'].map(str) + scores['m'].map(str)
    scores['compund_score'] = scores['r'] * weights[0] + scores['f'] * weights[1] + scores['m'] * weights[2]

    return scores
def run_RFM_analysis(frame, groups, weights):
    """
    run_RFM_analysis performs basic analysis in a two stage process
    :param
    frame:  Pandas DataFrame with core client info.
            Columns are: (sales,date,etc,etc)
    :return:
    scores
    """

    scores = create_scores(frame, groups, weights).reset_index()
    scores = assign_segment(scores)
    return scores
# def create_health_matrix(frame_in):
#     """'
#     Create_health_matrix visualizes in a 3x3 matrix, the composition of clients according to each segment
#     :param
#     frame_in:   Pandas DataFrame object with size (Nx2) where N is the # of clients.
#                 First column is client ID and second column is client segment
#     :return:
#     """
#     content = frame_in['segment'].value_counts().values.reshape(3, 3)
#     return content
# def explain_health_table(frame_in, sales_in):
#     """
#     :param frame_in:
#     :param sales_in:
#     :return:
#     """
#     frame_out = pd.DataFrame(np.ones((frame_in.shape[0], 6)),
#                              columns=['var_1', 'var_2', 'var_3', 'var_4', 'var_5', 'var_6'])
#     frame_out['client_id'] = frame_in['client_id']
#     frame_out = pd.merge(frame_in, frame_out, on='client_id', how='inner', validate='1:1').sort_values(
#         ['segment', 'client_id']).set_index('segment')
#     return frame_out
# def create_explanaiton_table(frame_in, sales_in):
#     """
#     :param frame_in:
#     :param sales_in:
#     :return:
#     """
#     frame_out = pd.DataFrame(np.ones((frame_in.shape[0], 6)),
#                              columns=['expl_1', 'expl_2', 'expl_3', 'expl_4', 'expl_5', 'expl_6'])
#     frame_out['client_id'] = frame_in['client_id']
#     frame_out = pd.merge(frame_in, frame_out, on='client_id', how='inner', validate='1:1').sort_values('client_id')
#     return frame_out
# def plot_single_importance(frame_in):
#     """
#     :param frame_in:
#     :return:
#     """
#     return sb.barplot(x='importance', y='factor',data=frame_in.melt(id_vars=['client_id', 'segment'], var_name='factor', value_name='importance'),palette='husl');

# Setting parameters
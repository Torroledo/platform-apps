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
    frame_out['client_name'] = 'Generic name'
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


def run_RFM_analysis(frame, n_groups, alpha):
    """
    run_RFM_analysis performs basic analysis in a two stage process
    :param
    frame:  Pandas DataFrame with core client info.
            Columns are: (sales,date,etc,etc)
    :return:
    scores
    """

    scores = create_scores(frame, n_groups, alpha)
    scores = assign_segment(scores)
    other_vars = create_other_vars(frame)

    return pd.merge(scores, other_vars, on='client_id', how='inner', validate='1:1')


def create_other_vars(frame_in):
    other_vars = frame_in.groupby('client_id').sum()['sales'].to_frame(name='sales')
    other_vars.reset_index(inplace=True)

    return other_vars


def create_scores(frame_in, groups, weights):
    """
    create_scores creates RFM scores for sales date (frame_in)
    :param
    frame_in:   Pandas DataFrame with core client info

    :return:
    scores:
    """
    today = pd.to_datetime(date.today())
    first_date = frame_in.groupby('client_id').min()['date'].to_frame(name='first_purchase')
    last_date = frame_in.groupby('client_id').max()['date'].to_frame(name='last_purchase')
    time_since_last = (today - last_date['last_purchase']).apply(lambda x: int(x.days / 30)).to_frame(
        name='months_since_last')

    # Verify calculation
    recency = (today - last_date).apply(lambda x: int(x[0].days / 30), axis=1).to_frame(name='recency')
    age = (today - first_date).apply(lambda x: int(x[0].days / 30), axis=1).to_frame(name='age')
    monetary = frame_in.groupby('client_id').max()['sales'].to_frame(name='monetary')
    # products = frame_in.groupby('client_id').agg({'product_id':np.size})['product_id'].to_frame(name='products')
    frequency = (((today - first_date).apply(lambda x: int(x[0].days / 30), axis=1)) / (
        frame_in.groupby('client_id').size())).to_frame(name='frequency')

    scores = pd.concat([recency, frequency, monetary, age], axis=1).apply(
        lambda x: pd.qcut(x, q=groups, labels=[i for i in range(1, groups + 1)], duplicates='raise').astype(int),
        axis=0)

    metrics = pd.concat([recency, frequency, monetary, age], axis=1)
    metrics.columns = [col + '_value' for col in metrics.columns]
    scores = pd.concat([scores, metrics], axis=1)

    scores = pd.concat([first_date, last_date, time_since_last, scores], axis=1)
    scores['score'] = scores['recency'] * weights[0] + scores['frequency'] * weights[1] + scores['monetary'] * weights[
        2] + scores['age'] * weights[3]
    scores['group'] = scores['recency'].map(str) + scores['frequency'].map(str) + scores['monetary'].map(str) + scores[
        'age'].map(str)
    scores['tenure'] = age['age']

    scores = scores.sort_values(by=['score'], ascending=False).reset_index()

    return scores# Setting parameters
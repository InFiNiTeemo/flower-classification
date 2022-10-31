import sys
# models
import pandas as pd
import re
import json
import ast
import time
from datetime import date, timedelta, datetime
import os

# utils
from ..CONSTANT.CONSTANTS import (
    MODEL_DIR,
    RANK_MODEL_DIR,
    RECALL_MODEL_DIR,
    DATASET_DIR,
    EMBEDDING_DIR,
    ONLINE_DF_COLUMNS,
    FEATS_DF_STR_COLUMNS,
    MIXED_DF_STR_COLUMNS
)

# feature processing functions

def apply_choose_rank_transform(df):
    col = 'choose_rank'
    print(df[col].isna().sum())
    df[col] = df[col].astype(str)
    df.dropna(subset=[col])
    df = df[df[col].str.isnumeric().fillna(0)]
    df[col] = df[col].astype(int)
    df = df[df[col] != -1]
    return df


class BaseModelPipeline:
    def __init__(self):
        # path
        self.model_dir = MODEL_DIR
        self.rank_model_dir = RANK_MODEL_DIR,
        self.recall_model_dir = RECALL_MODEL_DIR
        self.embedding_dir = EMBEDDING_DIR
        self.dataset_dir = DATASET_DIR
        self.search_record_csv_path = self.dataset_dir + os.sep + self.get_today_csv_name('search_record')
        self.online_df_path = self.dataset_dir + os.sep + self.get_today_csv_name('online_df')
        # df columns
        self.online_df_cols = ONLINE_DF_COLUMNS
        self.feats_df_str_cols = FEATS_DF_STR_COLUMNS
        self.mixed_df_str_cols = MIXED_DF_STR_COLUMNS

        self.model_dict = {}
        self.model = None
        self.seed = 2021

        self.debug = False

        pd.set_option('display.max_columns', None)

    def get_today_csv_name(self, header, csv_name=True):
        hour = time.localtime().tm_hour
        if hour <= 6:
            return self.get_yesterday_csv_name(header, csv_name)
        file_name = header + time.strftime('_%m_%d', time.localtime())
        if csv_name:
            file_name += '.csv'
        return file_name

    def get_yesterday_csv_name(self, header, csv_name):
        return header + (date.today() - timedelta(days=1)).strftime('_%m_%d') + ('.csv' if csv_name else '')

    def init_model(self):
        raise NotImplementedError

    def get_online_df(
            self,
            search_record_csv_path: str = None,
            online_df_csv_path: str = None
        ):
        """
        desc: get key cols from online search record
        """
        if online_df_csv_path is not None:
            return pd.read_csv(online_df_csv_path)
        df = pd.read_csv(search_record_csv_path)
        #df = df.sort_values(by='created_time', ascending=False)
        #df = df.loc[:5000]
        print(df.head())
        df = apply_choose_rank_transform(df)

        csv_fields = ['name', 'address', 'id']
        fields = ['choose_name', 'choose_addr', 'id', 'id_str']

        def get_user_chosen(x):
            rank = x[1]
            clean_data = True
            l, addr_dict = None, None
            id_str = ""
            try:
                # convert str list to list
                l = ast.literal_eval(x[0])
                addr_dict = l[rank]
                id_list = map(str, [d.get('id', None) for d in l if d.get('id', None) is not None])
                #print(id_list)
                id_str = '|'.join(id_list)
                #print(id_str)
                # print(id_list)
            except:
                clean_data = False

            if clean_data:
                try:
                    item_list = [addr_dict[field] for field in csv_fields]
                    # print(addr_dict.keys()); input()
                    item_list.append(id_str)
                    print(rank, *item_list)
                    #input()
                    return pd.Series(item_list, index=fields)
                    #return pd.Series([e, f, g], index=['a', 'b', 'c'])
                except:
                    clean_data = False
            return pd.Series([None]*len(fields), index=fields)

        df[fields] = df[['ai_resp', 'choose_rank']].apply(get_user_chosen, axis=1)
        df.dropna(subset=fields, inplace=True)

        df = df[self.online_df_cols]
        df.rename(columns={'keywords': 'user_input'}, inplace=True)
        print(df.head())
        print('before drop dup {}'.format(df.shape))
        # todo next version may not drop, use id to identify the search record
        df.drop_duplicates(subset=['user_input'], inplace=True)
        print('after drop dup {}'.format(df.shape))
        df.to_csv(self.online_df_path, index=True)
        # input()
        return df

    def get_online_recall_rate(self, online_df=None):
        if online_df is None:
            online_df = pd.read_csv(self.online_df_path)

        def filter_yesterday(create_time):
            print(create_time)
            time_obj = datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S')
            return (datetime.today() - time_obj).days <= 3

        filter = online_df['created_time'].apply(lambda x: filter_yesterday(x))
        online_df = online_df[filter]
        print(online_df[['created_time', 'choose_rank']].head(30))

        def topk_recall_rate(df, k):
            rate = len(df[(df['choose_rank'] <= k - 1)]) / len(df)
            print(f'recall@{k} rate {rate}')
            return "{:.2f}".format(rate)
        eval_criterion = {}
        recall_criterion = {}
        for k in range(5):
            recall_criterion['Top{}召回率'.format(k+1)] = topk_recall_rate(online_df, k + 1)
        eval_criterion['点击排名分数'] = recall_criterion
        eval_criterion['平均点击排名'] = "{:.2f}".format(online_df['choose_rank'].mean())
        eval_criterion['总点击次数'] = len(online_df)
        return eval_criterion


    def get_search_list(self, online_df):
        return online_df[['user_input','location']].values.tolist()

    def split_dataset(self, df:pd.DataFrame, label:str='', lr=.0, ur=.8, is_dump=False, time_label=None):
        if time_label is not None:
            #df = df.sort_values(by=time_label, ascending=False)
            #print(len(df), df.columns); print('\n'*5); print(df.head())
            df = df.drop(time_label, axis=1)
            #print(len(df), df.columns); print(df.head()); input('after_drop')
        df_tr, df_ts = df[int(len(df) * lr):int(len(df) * ur)], df[int(len(df) * ur):]
        if is_dump:
            self.dump_dataset(self.dump_dataset(df_tr, df_ts, 'sw_9'))
        y_tr, X_tr = df_tr[label], df_tr.drop([label], axis=1)
        y_ts, X_ts = df_ts[label], df_ts.drop([label], axis=1)
        return X_tr, y_tr, X_ts, y_ts

    def dump_dataset(self, X_tr, X_ts, name='1'):
        X_tr.to_csv('yiche_dataset/yiche_' + name + '_tr.csv', index=False)
        X_ts.to_csv('yiche_dataset/yiche_' + name + '_ts.csv', index=False)

    @staticmethod
    def shuffle_by_group(df, name=None):
        import random
        groups = [df for _, df in df.groupby(name)]
        random.shuffle(groups)
        return pd.concat(groups).reset_index(drop=True)

    def divide_numeric_and_string(self, df, str_cols):
        n_df, str_df = df.drop(str_cols, axis=1), df[str_cols]
        return n_df, str_df

    def preprocess_feats_df(self, feats_df):
        feats_df['source'] = feats_df['source'].apply(lambda x: 1 if x in ['gaode', 'gaode_poi'] else 0)
        # numeric or string
        n_df, str_df = self.divide_numeric_and_string(feats_df, self.feats_df_str_cols)
        return n_df, str_df

    def predict(self, feats_df):
        if feats_df is None:
            print('feats_df is None!!')
            input()
        n_df, str_df = self.preprocess_feats_df(feats_df)
        if self.debug:
            print('\n'*20)
            n_df_cols = n_df.columns.values
            model_cols = self.model.get_feature_name()
            print(n_df_cols,'\n', model_cols)
            print(set(n_df_cols)-set(model_cols))
            print(set(model_cols)-set(n_df_cols))
            # input()
        y_hats = self.model.predict_proba(n_df)
        # return [index:id, pred:score]
        y_hat = [x[0] for x in y_hats]
        y_hat = pd.DataFrame({'pred': y_hat})
        df = pd.concat([str_df['id'], y_hat], axis=1)
        df.set_index('id', inplace=True)
        return df




import os
import json
from datetime import date, timedelta, datetime

META = ".meta"
def save_attr(dir_path, field, value, force_reset=False):
    # force reset for not list type, such as int, float
    if not isinstance(value, str):
        value = str(value)
    # print('========',len(data),'=========')
    file_path = os.path.join(dir_path, META)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    d = {}
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                d = json.load(f)
                if str(value) not in d[field]:
                    d[field].append(value)
                if force_reset:
                    d[field] = [value]
                #print("page visited: ", d['page'])
            except:
                d[field] = [value]
    else:
        d[field] = [value]
    with open(file_path, "w+") as fw:
        json.dump(d, fw)


def get_attr(dir_path, field, default=None) -> list:
    file_path = os.path.join(dir_path, META)
    try:
        with open(file_path, "r") as f:
            d = json.load(f)
            return d[field]
            # print("page visited: ", d['page'])
    except:
        return default


def save_attr_with_timeliness(dir_path, field, value, valid_time=3):
    today = date.today().strftime('%y_%m_%d')
    save_attr(dir_path, field, "{}-{}-{}".format(value, today, valid_time))


def get_attr_with_timeliness(dir_path, field):
    """
    :param dir_path:
    :param field:
    :return: attr,  None for not valid
    """
    attrs = get_attr(dir_path, field)
    # check validation
    if attrs is None:
        return None
    value, d, valid_time = attrs[0].split("-")
    day = datetime.strptime(d, '%y_%m_%d').date()
    if date.today() <= day + timedelta(days=int(valid_time)):
        return value
    return None

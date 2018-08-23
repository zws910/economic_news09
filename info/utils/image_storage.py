from qiniu import Auth, put_data

access_key = "9lJvBVPBVr9zsiAz98jiMi_SN_tsJ55ewypsyhRq"
secret_key = "zqa1dUs0vJIOzMhXx_k_8S6-bdu_hm1MnqWZTJNx"
bucket_name = "ihome"


def storage(data):

    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e

    if info.status_code != 200:
        raise Exception("上传图片失败")

    return ret["key"]  # FrYe0pVVS-pGagmHeFvy71QZKsJT


if __name__ == '__main__':
    file = input('请输入文件路径')
    with open(file, 'rb') as f:
        storage(f.read())

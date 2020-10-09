import json
import time
import random
import requests

# 获取response.json dict
with open('./response.json', 'r', encoding='utf8')as fp:
    response_json = json.load(fp)
    college_all = response_json['data']['collegeAll']
    major_all = response_json['data']['majorAll']
    class_all = response_json['data']['classAll']


def main():
    """
    主函数
    """
    user_name = []
    user_id = []
    dept_text = []
    wx_uid = []
    # 输入Secrets
    user_in = input()
    while user_in != 'end':
        info = user_in.split(',')
        user_name.append(info[0])
        user_id.append(info[1])
        dept_text.append(info[2])
        wx_uid.append(info[3])
        user_in = input()

    # 时间判断 Github Actions采用国际标准时
    hms = update_time()
    if (hms[0] >= 12) & (hms[0] < 14):
        customer_app_type_rule_id = 147
   
    else:
        print('未到打卡时间，将重打早间卡测试')
        customer_app_type_rule_id = 146

    for index, value in enumerate(user_id):
        time_msg = str(hms[0]) + '时' + str(hms[1]) + '分' + str(hms[2]) + '秒'
        response = check_in(user_name[index],
                            user_id[index],
                            dept_text[index],
                            customer_app_type_rule_id)
        if '成功' in response:
            title = value[-4:] + ' ' + time_msg + '打卡成功'
        else:
            title = value[-4:] + ' ' + time_msg + '打卡失败，请手动补卡'
        print(title)
        wx_push(wx_uid[index], title, response)
        hms = update_time()


def print_info_error():
    """
    打印 个人信息错误
    """
    print('请检查你填写的个人信息！')
    print('如:')
    print('小明,201912340101,理学院-应用物理学-应物1901,UID_abcdefghijklm')
    print('end')


def update_time():
    return [(time.localtime().tm_hour + 8) % 24,
            time.localtime().tm_min,
            time.localtime().tm_sec]


def get_class_id(dept_text):
    # 获取学院、专业和班级信息
    try:
        info = dept_text.split('-', 3)
        college_name = info[0]
        major_name = info[1]
        class_name = info[2]
    except IndexError:
        print_info_error()
        exit(1)

    # 获取deptId
    try:
        for college in college_all:
            if college['name'] == college_name:
                college_id = college['deptId']
                break
        for major in major_all:
            if (major['name'] == major_name) & (major['parentId'] == college_id):
                major_id = major['deptId']
                break
        for class_ in class_all:
            if (class_['name'] == class_name) & (class_['parentId'] == major_id):
                class_id = class_['deptId']
                break
        if class_id:
            print()
    except NameError:
        print_info_error()
        exit(1)
    return class_id


def switch_customer_app_type_rule_id(customer_app_type_rule_id):
    switcher = {
        146: 'clockSign1',
        147: 'clockSign2',
        148: 'clockSign3'
    }
    return switcher.get(customer_app_type_rule_id, "nothing")


def get_check_json(stu_name, stu_id, dept_text, customer_app_type_rule_id):
    # 随机温度(36.2~36.5)
    a = random.uniform(36.2, 36.5)
    temperature = round(a, 1)
    class_id = get_class_id(dept_text)
    template_id = switch_customer_app_type_rule_id(customer_app_type_rule_id)
    return {
        "businessType": "epmpics",
        "method": "submitUpInfoSchool",
        "jsonData": {
            "deptStr": {
                "deptid": class_id,
                "text": dept_text
            },
            "areaStr": {"streetNumber": "", "street": "长椿路辅路", "district": "中原区", "city": "郑州市", "province": "河南省",
                        "town": "", "pois": "河南工业大学(莲花街校区)", "lng": 113.544407 + random.random() / 10000,
                        "lat": 34.831014 + random.random() / 10000, "address": "中原区长椿路辅路河南工业大学(莲花街校区)",
                        "text": "河南省-郑州市", "code": ""},
            "reportdate": round(time.time() * 1000),
            "customerid": 43,
            "deptid": class_id,
            "source": "app",
            "templateid": template_id,
            "stuNo": stu_id,
            "username": stu_name,
            "userid": round(time.time()),
            "updatainfo": [
                {
                    "propertyname": "temperature",
                    "value": temperature
                },
                {
                    "propertyname": "symptom",
                    "value": "无症状"
                }
            ],
            "customerAppTypeRuleId": customer_app_type_rule_id,
            "clockState": 0
        },
    }


def check_in(stu_name, stu_id, dept_text, customer_app_type_rule_id):
    # 获取打卡URL及JSON
    check_url = "https://reportedh5.17wanxiao.com/sass/api/epmpics"
    check_json = get_check_json(stu_name, stu_id, dept_text, customer_app_type_rule_id)

    # 提交打卡与结果返回
    for i in range(1, 10):
        response = requests.post(check_url, json=check_json)
        if response.status_code == 200:
            break
        else:
            time.sleep(30)
    print(response.text)
    return response.text


def wx_push(wx_uid, title, response):
    # 微信通知
    wx_pusher_url = 'http://wxpusher.zjiecode.com/api/send/message'
    content = f"""
    
```
{response}
```

### 💴扫码捐赠一杯咖啡
<center><img src="https://s1.ax1x.com/2020/09/16/w25Jxg.png"/></center>
### 😢[反馈](https://github.com/chillsoul/EzCheckInSchool/issues)
### 😀[记得Star此项目](https://github.com/chillsoul/EzCheckInSchool)
        """
    data = {
        "appToken": "AT_bVK4MZob9c9acNmLbWHN6RjQxeGllOOB",
        "content": content,
        "summary": title,
        "contentType": 3,
        "uids": [wx_uid]
    }
    response = requests.post(wx_pusher_url, json=data)


if __name__ == '__main__':
    main()

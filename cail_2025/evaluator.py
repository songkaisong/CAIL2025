# encoding=utf-8
import traceback
import requests
import json
import os
import argparse
from copy import deepcopy
log_txt = ""

"""
主观题打分
Args:
    _instance (dict): 评测样例
     {
        big_ques (str): 大问,
        small_ques (str): 小问,
        user_answer (str): 用户答案,
        ground_answer (str): 标准答案,
        score (int): 分值,
        score_point (str): 采分点说明
     }

Returns:
    float: 模型评分
"""

def tongyi_score(ground_truth, prediction):
    url = "https://nlp-cn-beijing.aliyuncs.com/v1/services/fastagi/chat/completions"
    headers = {
        "authority": "nlp-daily.aliyuncs.com",
        "Content-Type": "application/json",
        "Authorization": "Bearer lm-4HBAz9G3gLbD3J4Nkj3qbg==",
        "x-fag-appcode": "llm_test",
        "x-fag-servicename": "llm_test-farui",
        "X-DashScope-DataInspection": json.dumps({"input": "disable", "output": "disable"}),
    }

    truncate_length = int(len(ground_truth["ground_answer"]) * 2)
    new_prediction = deepcopy(prediction)
    new_prediction["user_answer"] = new_prediction["user_answer"][:truncate_length]

    data = {
        "ground_truth": ground_truth,
        "prediction": new_prediction
    }

    response = requests.post(url, json=data, headers=headers)
    # 检查响应状态码并打印响应内容
    if response.status_code == 200:
        predicted_score = response.json()["predicted_score"]
        return predicted_score
    else:
        log_txt.write("评分模型调用失败！\n")
        log_txt.write(f"HTTP返回码：{response.status_code}\n")
        log_txt.flush()
        raise Exception("评分模型调用失败！")


"""
加载真实答案
Args:
    file_path (str): 真实答案文件路径

Returns:
    dict: 真实答案字典, key=id, value={big_ques, small_ques, ground_answer, score, score_point}
"""


def load_ground_truth(file_path):
    print(file_path)
    try:
        ground_truth_records = open(file_path).readlines()
        ground_truth_dict = dict()
        for record in ground_truth_records:
            j = json.loads(record)
            ground_truth_dict[j["id"]] = j
        return ground_truth_dict
    except Exception as e:
        log_txt.write(traceback.format_exc())
        log_txt.write("标准答案加载错误！\n")
        log_txt.flush()
        raise ValueError("标准答案加载错误！")


"""
加载预测答案
Args:
    file_path (str): 预测答案文件路径

Returns:
    dict: 预测答案字典，key=id, value=user_answer
"""


def load_prediction(file_path):
    try:
        prediction_dict = dict()
        lines = open(file_path).readlines()
        for line in lines:
            j = json.loads(line)
            prediction_dict[j["id"]] = j
        return prediction_dict
    except Exception as e:
        log_txt.write(traceback.format_exc())
        log_txt.write("测试文件加载错误！\n")
        log_txt.flush()
        raise ValueError("测试文件加载错误！")


"""
主观题打分
Args:
    prediction_dict (dict): 预测答案,
    ground_truth_dict (dict): 标准答案

Returns:
    None
"""


def check_file_validity(prediction_dict, ground_truth_dict):
    prediction_keys = set(prediction_dict.keys())
    ground_truth_keys = set(ground_truth_dict.keys())
    if len(prediction_keys) != len(ground_truth_keys):
        log_txt.write("回答题目数目和标准答案不一致！\n")
        log_txt.flush()
        raise ValueError("回答题目数目和标准答案不一致！")
    if prediction_keys != ground_truth_keys:
        log_txt.write("回答题目编号和标准答案不一致！\n")
        log_txt.flush()
        raise ValueError("回答题目编号和标准答案不一致！")


"""
主观题打分
Args:
    base_dir (str): 根路径,
    pred_file (str): 选手提交的文件路径,
    stage_index (int): 0:初赛，1:复赛，2:封赛

Returns:
    None
"""


def evaluate(base_dir, pred_file, stage_index):
    try:
        # 读取赛道目录下的ground_truth，通过后缀区分不同阶段，0、1、2分别表示初赛、复赛和封赛，例如初赛为ground_truth_0.json
        ground_truth = load_ground_truth(
            os.path.join(base_dir, "ground_truth_" + str(stage_index) + ".json")
        )
        # 读取参赛选手上传的预测文件，默认第一个文件为最新上传文件
        prediction = load_prediction(pred_file)
        # 检查上传文件内容和格式
        check_file_validity(prediction, ground_truth)
        # 遍历测试文件，开始测试
        score_list = []
        user_score = 0
        total_score = 0
        for index, (id, prediction_item) in enumerate(prediction.items()):
            log_txt.write(f"{'=*' * 5}第{index}/{len(prediction.keys())}题：qid={id}{'=*' * 5}\n")
            ground_truth_item = deepcopy(ground_truth[id])
            log_txt.write(f"调用评分模型\n")
            score = tongyi_score(ground_truth_item, prediction_item)
            log_txt.write(f"评分结果：{score} \n{'=*' * 15}\n")
            log_txt.flush()
            score = min(score, ground_truth_item["score"])
            total_score += ground_truth_item["score"]
            print("score", score)
            score_list.append((id, score))
            user_score += score
    except Exception as e:
        log_txt.write(traceback.format_exc())
        log_txt.write("\n")
        log_txt.flush()
        return {"error_info": str(e)}
    return {
        "score": {
            "scoring_ratio": round((user_score/total_score)*100, 4),
            "user_score": user_score,
            "total_score": total_score,
            "details": ";".join(
                [
                    item[0] + ":" + str(item[1])
                    for item in sorted(
                        score_list, key=lambda x: eval(x[0].split("_")[-1])
                    )
                ]
            ),
        },
        "error_info": "",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="sfkszgt")
    parser.add_argument("--base_dir", type=str, required=False, help="base dir", default="./")
    parser.add_argument(
        "--pred_file", type=str, required=False, help="prediction file path", default="./prediction.json"
    )
    parser.add_argument(
        "--stage_index", type=int, required=False, help="0:初赛，1:复赛，2:封赛", default=0
    )
    parser.add_argument("--log_file", type=str, required=False, help="log file path", default="../log")
    args = parser.parse_args()
    log_path = args.log_file
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_txt = open(log_path, "a")
    result = evaluate(
        base_dir=args.base_dir, pred_file=args.pred_file, stage_index=args.stage_index
    )
    print(json.dumps(result, ensure_ascii=False))

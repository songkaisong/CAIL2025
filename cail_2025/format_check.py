import json
import requests


def call_user_api(api_url, test_file):
    lines = open(test_file).readlines()
    result = []
    for line in lines:
        j = json.loads(line)
        input_data = {
            "id": j["id"],
            "big_ques": j["big_ques"],
            "small_ques": j["small_ques"],
            "score": j["score"]
        }
        response = requests.post(api_url, json=input_data)
        record = response.json()
        if "id" not in record or record["id"] != input_data["id"]:
            raise Exception(input_data["id"] + " does not exist.")
        if "user_answer" not in record or record["user_answer"] is None or record["user_answer"] == "":
            raise Exception(input_data["id"] + " has no valid answer.")
        result.append(record)
    return result


if __name__ == '__main__':
    api_url = "add your api url"
    call_user_api(api_url, "test_data.json")
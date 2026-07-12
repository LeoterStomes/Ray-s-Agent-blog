from typing import Optional

class Result:
    @staticmethod
    def success(data=None, msg="操作成功"):
        return {"code": "200", "msg": msg, "data": data}
    @staticmethod
    def error(msg="操作失败", code="500"):
        return {"code": code, "msg": msg, "data": None}

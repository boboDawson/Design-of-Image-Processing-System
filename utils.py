import re

def validate_password(password, min_length=8, need_upper=True, need_lower=True,
                     need_digit=True, need_special=True):
    """
    可配置的密码验证函数
    """
    if len(password) < min_length:
        return False, f"密码长度至少为{min_length}位"

    if need_upper and not re.search(r'[A-Z]', password):
        return False, "密码必须包含大写字母"

    if need_lower and not re.search(r'[a-z]', password):
         return False, "密码必须包含小写字母"

    if need_digit and not re.search(r'\d', password):
         return False, "密码必须包含数字"

    if need_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
         return False, "密码必须包含特殊符号"

    return True, "密码符合要求"

# 未来可以添加其他通用的工具函数到这里 
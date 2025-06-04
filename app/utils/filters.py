
import re
from markupsafe import Markup

def strip_images_filter(html_content):
    """HTML에서 이미지 태그 제거"""
    if html_content is None:
        return ''
    cleaned_content = re.sub(r'<img(?:\s[^>]*)?>', '', str(html_content), flags=re.IGNORECASE)
    return cleaned_content

def nl2br_filter(s):
    """개행 문자를 <br> 태그로 변환"""
    if s is None:
        return ''
    return Markup(str(s).replace('\n', '<br>\n'))

def mask_ip_filter(ip_address_str):
    """IP 주소 마스킹"""
    if not ip_address_str:
        return "N/A"
    parts = ip_address_str.split('.')
    if len(parts) == 4:  # IPv4
        return f"{parts[0]}.{parts[1]}.X.X"
    elif ':' in ip_address_str:  # IPv6
        return "IPv6 Address"
    return "Invalid IP"

def register_template_filters(app):
    """템플릿 필터 등록"""
    app.jinja_env.filters['strip_images'] = strip_images_filter
    app.jinja_env.filters['nl2br'] = nl2br_filter
    app.jinja_env.filters['mask_ip'] = mask_ip_filter

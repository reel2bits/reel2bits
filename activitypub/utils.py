from flask import current_app


def ap_url(klass, username):
    if klass == "url":
        return f"https://{current_app.config['AP_DOMAIN']}/user/{username}"
    elif klass == "shared_inbox":
        return f"https://{current_app.config['AP_DOMAIN']}/inbox"
    elif klass == "inbox":
        return f"https://{current_app.config['AP_DOMAIN']}" \
               f"/user/{username}/inbox"
    elif klass == "outbox":
        return f"https://{current_app.config['AP_DOMAIN']}" \
               f"/user/{username}/outbox"
    else:
        return None


def full_url(path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    root = current_app.config['AP_DOMAIN']
    if path.startswith('/'):
        return root + path[1:]
    elif path.startswith('/'):
        return root + "/" + path
    else:
        return root + path

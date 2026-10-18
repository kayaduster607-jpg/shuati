from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import uuid
import hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='static')
CORS(app)

DATA_DIR = os.environ.get('DATA_DIR', '/data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
ADMIN_SETUP_FILE = os.path.join(DATA_DIR, 'admin_setup.json')

# Token 存储（内存中，重启失效，用户需重新登录）
tokens = {}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def read_json(path, default=None):
    if default is None:
        default = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def gen_id():
    return uuid.uuid4().hex[:12]


def get_users():
    return read_json(USERS_FILE, [])


def save_users(users):
    write_json(USERS_FILE, users)


def get_user_data_path(user_id, filename):
    return os.path.join(DATA_DIR, 'userdata', user_id, f'{filename}.json')


def read_user_data(user_id, filename, default=None):
    if default is None:
        default = []
    path = get_user_data_path(user_id, filename)
    return read_json(path, default)


def write_user_data(user_id, filename, data):
    path = get_user_data_path(user_id, filename)
    write_json(path, data)


def get_current_user():
    """从请求中获取当前用户"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None
    user_id = tokens.get(token)
    if not user_id:
        return None
    users = get_users()
    for u in users:
        if u['id'] == user_id:
            return u
    return None


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': '未登录'}), 401
        return f(user, *args, **kwargs)
    return decorated


def admin_required(f):
    """管理员验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': '未登录'}), 401
        if user.get('role') != 'admin':
            return jsonify({'error': '无权限'}), 403
        return f(user, *args, **kwargs)
    return decorated


# ========== 初始化默认用户 ==========

def init_users():
    users = get_users()
    if not users:
        # 创建默认用户
        default_users = [
            {
                'id': 'admin1',
                'username': 'admin',
                'password': hash_password('admin123'),
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'user1',
                'username': 'user',
                'password': hash_password('123456'),
                'role': 'user',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'user2',
                'username': 'user2',
                'password': hash_password('123456'),
                'role': 'user',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'user3',
                'username': 'user3',
                'password': hash_password('123456'),
                'role': 'user',
                'created_at': datetime.now().isoformat()
            }
        ]
        save_users(default_users)
        print("已创建默认用户：admin/admin123（管理员）, user/123456, user2/123456, user3/123456")


init_users()


# ========== Auth API ==========

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')

    users = get_users()
    for u in users:
        if u['username'] == username and u['password'] == hash_password(password):
            token = uuid.uuid4().hex
            tokens[token] = u['id']
            return jsonify({
                'token': token,
                'user': {
                    'id': u['id'],
                    'username': u['username'],
                    'role': u['role']
                }
            })

    return jsonify({'error': '用户名或密码错误'}), 401


@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_me(user):
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'role': user['role']
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    tokens.pop(token, None)
    return jsonify({'success': True})


@app.route('/api/auth/change-password', methods=['POST'])
@login_required
def change_password(user):
    data = request.json
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if user['password'] != hash_password(old_password):
        return jsonify({'error': '原密码错误'}), 400

    users = get_users()
    for u in users:
        if u['id'] == user['id']:
            u['password'] = hash_password(new_password)
            break
    save_users(users)
    return jsonify({'success': True})


# ========== Admin API ==========

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users(user):
    users = get_users()
    return jsonify([{
        'id': u['id'],
        'username': u['username'],
        'role': u['role'],
        'created_at': u.get('created_at', '')
    } for u in users])


@app.route('/api/admin/users', methods=['POST'])
@admin_required
def admin_create_user(user):
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    users = get_users()
    for u in users:
        if u['username'] == username:
            return jsonify({'error': '用户名已存在'}), 400

    new_user = {
        'id': gen_id(),
        'username': username,
        'password': hash_password(password),
        'role': role,
        'created_at': datetime.now().isoformat()
    }
    users.append(new_user)
    save_users(users)
    return jsonify({'success': True, 'user': {
        'id': new_user['id'],
        'username': new_user['username'],
        'role': new_user['role']
    }})


@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user, user_id):
    if user['id'] == user_id:
        return jsonify({'error': '不能删除自己'}), 400

    users = get_users()
    users = [u for u in users if u['id'] != user_id]
    save_users(users)

    # 删除用户数据
    import shutil
    user_data_dir = os.path.join(DATA_DIR, 'userdata', user_id)
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir)

    return jsonify({'success': True})


@app.route('/api/admin/users/<user_id>/reset-password', methods=['POST'])
@admin_required
def admin_reset_password(user, user_id):
    data = request.json
    new_password = data.get('password', '123456')

    users = get_users()
    for u in users:
        if u['id'] == user_id:
            u['password'] = hash_password(new_password)
            break
    save_users(users)
    return jsonify({'success': True})


@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats(user):
    users = get_users()
    stats = []
    for u in users:
        banks = read_user_data(u['id'], 'banks')
        questions = read_user_data(u['id'], 'questions')
        records = read_user_data(u['id'], 'records')
        stats.append({
            'user_id': u['id'],
            'username': u['username'],
            'role': u['role'],
            'banks_count': len(banks),
            'questions_count': len(questions),
            'records_count': len(records)
        })
    return jsonify(stats)


# ========== Banks API ==========

@app.route('/api/banks', methods=['GET'])
@login_required
def get_banks(user):
    return jsonify(read_user_data(user['id'], 'banks'))


@app.route('/api/banks', methods=['POST'])
@login_required
def create_bank(user):
    data = request.json
    banks = read_user_data(user['id'], 'banks')
    bank = {
        'id': gen_id(),
        'name': data.get('name', ''),
        'description': data.get('description', ''),
        'created_at': datetime.now().isoformat()
    }
    banks.insert(0, bank)
    write_user_data(user['id'], 'banks', banks)
    return jsonify(bank)


@app.route('/api/banks/<bank_id>', methods=['DELETE'])
@login_required
def delete_bank(user, bank_id):
    banks = read_user_data(user['id'], 'banks')
    banks = [b for b in banks if b['id'] != bank_id]
    write_user_data(user['id'], 'banks', banks)

    questions = read_user_data(user['id'], 'questions')
    questions = [q for q in questions if q['bank_id'] != bank_id]
    write_user_data(user['id'], 'questions', questions)

    return jsonify({'success': True})


# ========== Questions API ==========

@app.route('/api/questions', methods=['GET'])
@login_required
def get_all_questions(user):
    bank_id = request.args.get('bank_id')
    questions = read_user_data(user['id'], 'questions')
    if bank_id:
        questions = [q for q in questions if q['bank_id'] == bank_id]
    return jsonify(questions)


@app.route('/api/questions', methods=['POST'])
@login_required
def add_questions(user):
    data = request.json
    bank_id = data.get('bank_id')
    new_questions = data.get('questions', [])

    questions = read_user_data(user['id'], 'questions')

    existing_contents = set()
    for q in questions:
        if q['bank_id'] == bank_id:
            key = q['content'].strip().replace(' ', '').lower()
            existing_contents.add(key)

    added = 0
    skipped = 0
    for q in new_questions:
        key = q.get('content', '').strip().replace(' ', '').lower()
        if key in existing_contents:
            skipped += 1
            continue

        question = {
            'id': gen_id(),
            'bank_id': bank_id,
            'type': q.get('type', 'single_choice'),
            'content': q.get('content', ''),
            'options': q.get('options'),
            'answer': q.get('answer', ''),
            'explanation': q.get('explanation', ''),
            'source_file': q.get('source_file', '')
        }
        questions.append(question)
        existing_contents.add(key)
        added += 1

    write_user_data(user['id'], 'questions', questions)
    return jsonify({'added': added, 'skipped': skipped})


@app.route('/api/questions/<question_id>', methods=['PUT'])
@login_required
def update_question(user, question_id):
    data = request.json
    questions = read_user_data(user['id'], 'questions')

    for i, q in enumerate(questions):
        if q['id'] == question_id:
            questions[i].update({
                'type': data.get('type', q['type']),
                'content': data.get('content', q['content']),
                'options': data.get('options', q['options']),
                'answer': data.get('answer', q['answer']),
                'explanation': data.get('explanation', q['explanation'])
            })
            break

    write_user_data(user['id'], 'questions', questions)
    return jsonify({'success': True})


@app.route('/api/questions/<question_id>', methods=['DELETE'])
@login_required
def delete_question(user, question_id):
    questions = read_user_data(user['id'], 'questions')
    questions = [q for q in questions if q['id'] != question_id]
    write_user_data(user['id'], 'questions', questions)
    return jsonify({'success': True})


# ========== Records API ==========

@app.route('/api/records', methods=['GET'])
@login_required
def get_records(user):
    return jsonify(read_user_data(user['id'], 'records'))


@app.route('/api/records', methods=['POST'])
@login_required
def add_records(user):
    data = request.json
    records_list = data.get('records', [])
    records = read_user_data(user['id'], 'records')

    for r in records_list:
        records.append({
            'question_id': r.get('question_id'),
            'is_correct': r.get('is_correct'),
            'user_answer': r.get('user_answer', ''),
            'answered_at': r.get('answered_at', datetime.now().isoformat())
        })

    write_user_data(user['id'], 'records', records)
    return jsonify({'success': True, 'count': len(records_list)})


# ========== Saved Practice API ==========

@app.route('/api/saved-practice', methods=['GET'])
@login_required
def get_saved_practice(user):
    data = read_user_data(user['id'], 'saved_practice', default=None)
    return jsonify(data)


@app.route('/api/saved-practice', methods=['PUT'])
@login_required
def save_practice(user):
    data = request.json
    write_user_data(user['id'], 'saved_practice', data)
    return jsonify({'success': True})


@app.route('/api/saved-practice', methods=['DELETE'])
@login_required
def clear_saved_practice(user):
    path = get_user_data_path(user['id'], 'saved_practice')
    if os.path.exists(path):
        os.remove(path)
    return jsonify({'success': True})


# ========== Serve Frontend ==========

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)

from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from PIL import Image
from pyzbar.pyzbar import decode
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 请替换为您的密钥

# 配置文件上传
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tif', 'tiff', 'jfif', 'pjpeg', 'pjp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件的最大大小为16MB

# 确保上传文件夹存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 检查文件是否允许的扩展名
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 首页，显示上传表单
@app.route('/')
def index():
    return render_template('index.html')

# 处理文件上传和二维码解析
@app.route('/upload', methods=['POST'])
def upload():
    if 'files[]' not in request.files:
        flash('没有文件部分')
        return redirect(url_for('index'))

    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        flash('未选择任何文件')
        return redirect(url_for('index'))

    urls = []
    failed_files = []

    for file in files:
        if file and allowed_file(file.filename):
            # 为文件名添加唯一标识，防止同名文件冲突
            unique_filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                file.save(filepath)

                # 解析二维码
                img = Image.open(filepath)
                decoded_objects = decode(img)
                if decoded_objects:
                    for obj in decoded_objects:
                        urls.append(obj.data.decode('utf-8'))
                else:
                    failed_files.append(file.filename)
            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                failed_files.append(file.filename)
            finally:
                # 处理完后删除文件，节省存储空间
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            failed_files.append(file.filename)

    # 比较URL，统计结果
    url_counts = {}
    for url in urls:
        if url in url_counts:
            url_counts[url] += 1
        else:
            url_counts[url] = 1

    # 判断是否所有URL都相同
    all_same_url = len(url_counts) == 1 and len(urls) > 0

    return render_template('result.html', urls=urls, url_counts=url_counts, failed_files=failed_files, all_same_url=all_same_url)

# 自定义错误处理页面（可选）
@app.errorhandler(413)
def request_entity_too_large(error):
    return '文件太大，超过了限制！', 413

if __name__ == '__main__':
    app.run(debug=True)

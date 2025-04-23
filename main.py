from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  # ✅ 'pp' değil, 'app' kullan
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kocakadmin:4Zj7NIKIMpmdh1EOaxXNNeMqV6sFmiFI@dpg-d048kpi4d50c739u7ngg-a/kocakegitim'

db = SQLAlchemy(app)


# MODELLER
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class LiveClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VideoRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    embed_code = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReferenceCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    used = db.Column(db.Boolean, default=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='yesilsogan')
        db.session.add(admin)
        db.session.commit()

def convert_youtube_link_to_iframe(url):
    if 'watch?v=' in url:
        video_id = url.split('watch?v=')[-1]
        return f'<iframe width="100%" height="300" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
    return url

@app.route('/test')
def test():
    try:
        codes = ReferenceCode.query.all()
        return f"{len(codes)} referans kodu bulundu."
    except Exception as e:
        return f"HATA: {e}"





@app.route('/')
def index():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('index.html', announcements=announcements)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user'] = username
            return redirect('/')
        else:
            flash('Kullanıcı adı veya şifre hatalı')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        refcode = request.form['refcode']
        code = ReferenceCode.query.filter_by(code=refcode, used=False).first()
        if code:
            existing = User.query.filter_by(username=username).first()
            if existing:
                flash('Bu kullanıcı adı zaten alınmış.')
            else:
                user = User(username=username, password=password)
                db.session.add(user)
                code.used = True
                db.session.commit()
                flash('Kayıt başarılı!')
                return redirect('/login')
        else:
            flash('Geçersiz veya kullanılmış referans kodu')
    return render_template('register.html')

@app.route('/live-classes')
def live_classes():
    if 'user' not in session:
        return redirect(url_for('login'))
    classes = LiveClass.query.order_by(LiveClass.created_at.desc()).all()
    return render_template('live_classes.html', classes=classes)

@app.route('/recordings')
def recordings():
    if 'user' not in session:
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    per_page = 3
    pagination = VideoRecord.query.order_by(VideoRecord.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('recordings.html', pagination=pagination)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'live_title' in request.form:
            live = LiveClass(title=request.form['live_title'], url=request.form['live_url'])
            db.session.add(live)
            db.session.commit()
        elif 'record_title' in request.form:
            raw_code = request.form['embed_code']
            final_code = convert_youtube_link_to_iframe(raw_code)
            record = VideoRecord(title=request.form['record_title'], embed_code=final_code)
            db.session.add(record)
            db.session.commit()
        elif 'ref_code' in request.form:
            existing = ReferenceCode.query.filter_by(code=request.form['ref_code']).first()
            if existing:
                flash('Bu referans kodu zaten var.')
            else:
                code = ReferenceCode(code=request.form['ref_code'])
                db.session.add(code)
                db.session.commit()
        elif 'announcement_text' in request.form:
            text = request.form['announcement_text']
            print("📢 Yeni duyuru eklendi:", text)
            ann = Announcement(text=text)
            db.session.add(ann)
            db.session.commit()
        elif 'delete_announcement' in request.form:
            ann = Announcement.query.get(request.form['delete_announcement'])
            if ann:
                db.session.delete(ann)
                db.session.commit()
        elif 'delete_live' in request.form:
            cls = LiveClass.query.get(request.form['delete_live'])
            if cls:
                db.session.delete(cls)
                db.session.commit()
        elif 'delete_record' in request.form:
            rec = VideoRecord.query.get(request.form['delete_record'])
            if rec:
                db.session.delete(rec)
                db.session.commit()
        elif 'delete_user' in request.form:
            user = User.query.get(request.form['delete_user'])
            if user and user.username != 'admin':
                db.session.delete(user)
                db.session.commit()

    live_classes = LiveClass.query.order_by(LiveClass.created_at.desc()).all()
    video_records = VideoRecord.query.order_by(VideoRecord.created_at.desc()).all()
    reference_codes = ReferenceCode.query.all()
    users = User.query.filter(User.username != 'admin').all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    print("📝 Tüm duyurular:", announcements)

    return render_template(
        'admin.html',
        live_classes=live_classes,
        video_records=video_records,
        reference_codes=reference_codes,
        users=users,
        announcements=announcements
    )

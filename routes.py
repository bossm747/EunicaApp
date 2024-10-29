from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Band, BandMembership, Message
from datetime import datetime

@app.route('/')
@login_required
def index():
    return redirect(url_for('chat'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email']
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    bands = Band.query.join(BandMembership).filter(
        BandMembership.user_id == current_user.id
    ).all()
    return render_template('chat.html', bands=bands)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/band/create', methods=['POST'])
@login_required
def create_band():
    band = Band(name=request.form['name'])
    db.session.add(band)
    membership = BandMembership(user=current_user, band=band)
    db.session.add(membership)
    db.session.commit()
    return redirect(url_for('chat'))

@app.route('/search_messages', methods=['GET'])
@login_required
def search_messages():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    messages = Message.query.filter(
        Message.content.ilike(f'%{query}%'),
        Message.chatroom.has(ChatRoom.users.any(id=current_user.id))
    ).order_by(Message.timestamp.desc()).all()

    results = []
    for message in messages:
        results.append({
            'id': message.id,
            'content': message.content,
            'username': message.sender.username,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'chat_id': message.chatroom_id
        })

    return jsonify({'results': results})

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    chat_id = request.form.get('chat_id')
    message_content = request.form.get('message', '').strip()
    file = request.files.get('file')

    if not chat_id:
        return jsonify({'error': 'Chat ID is required'}), 400

    chatroom = ChatRoom.query.get(chat_id)
    if not chatroom or current_user not in chatroom.users:
        return jsonify({'error': 'Invalid chat room or unauthorized access'}), 403

    message_type = 'text'
    file_path = None
    file_name = None

    if file:
        file_name = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        file.save(file_path)
        message_type = 'file' if file_name.split('.')[-1] not in ['png', 'jpg', 'jpeg', 'gif'] else 'image'

    message = Message(
        content=message_content,
        message_type=message_type,
        file_path=file_path,
        file_name=file_name,
        sender_id=current_user.id,
        chatroom_id=chat_id
    )

    db.session.add(message)
    db.session.commit()

    message_data = {
        'message': message.content,
        'message_type': message.message_type,
        'file_path': url_for('static', filename=file_path) if file_path else None,
        'file_name': file_name,
        'username': current_user.username,
        'sender_id': current_user.id,
        'timestamp': message.timestamp.strftime('%H:%M')
    }

    socketio.emit('new_message', message_data, room=str(chat_id))

    return jsonify({'success': True})

from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio, db
from models import Message, Band, ChatRoom

@socketio.on('join')
def on_join(data):
    room = data['band_id']
    join_room(room)
    emit('status', {'msg': f'{current_user.username} has joined the band chat'}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['band_id']
    leave_room(room)
    emit('status', {'msg': f'{current_user.username} has left the band chat'}, room=room)

@socketio.on('message')
def handle_message(data):
    if not current_user.is_authenticated:
        return
    
    message = Message(
        content=data['message'],
        user_id=current_user.id,
        band_id=data['band_id']
    )
    db.session.add(message)
    db.session.commit()
    
    emit('message', {
        'message': message.content,
        'username': current_user.username,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    }, room=data['band_id'])

@socketio.on('search_messages')
def handle_search_messages(data):
    query = data.get('query', '').strip()
    if not query:
        emit('search_results', {'error': 'Query parameter is required'}, room=f'user_{current_user.id}')
        return

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

    emit('search_results', {'results': results}, room=f'user_{current_user.id}')

# Simple conversation memory

conversation_history = []


def add_message(role, message):
    conversation_history.append({"role": role, "message": message})

    # Keep only the last 10 messages
    if len(conversation_history) > 10:
        conversation_history.pop(0)


def get_context():
    if not conversation_history:
        return ""

    context = ""

    for chat in conversation_history:
        context += f"{chat['role']}: {chat['message']}\n"

    return context


def clear_memory():
    conversation_history.clear()

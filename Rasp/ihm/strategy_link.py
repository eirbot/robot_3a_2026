from queue import Queue

ui_queue: Queue = Queue()

# Messages:
# {"type": "score", "value": int}
# {"type": "error", "value": bool}
# {"type": "end_match"}


def update_score(value: int):
    ui_queue.put({"type": "score", "value": int(value)})


def set_error(flag: bool):
    ui_queue.put({"type": "error", "value": bool(flag)})


def end_match():
    ui_queue.put({"type": "end_match"})
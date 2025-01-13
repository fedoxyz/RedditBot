import threading

def run_in_threads(players, method, synchronize=False, *args, **kwargs):
    if not isinstance(players, list):
        players = [players]  # Convert single object to a list
    threads = []
    barrier = threading.Barrier(len(players)) if synchronize else None

    def thread_func(player):
        getattr(player, method)(*args, **kwargs)
        if synchronize:
            barrier.wait()

    for player in players:
        thread = threading.Thread(target=thread_func, args=(player,))
        threads.append(thread)
        thread.start()

    if not synchronize:
        return

    for thread in threads:
        thread.join()


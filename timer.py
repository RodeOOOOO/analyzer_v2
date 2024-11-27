import time

def timer_thread(shared_data, flow_lock):
    """Thread to keep track of elapsed time and possibly change flow or valve modes."""
    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time
        with flow_lock:
            shared_data["elapsed_time"] = elapsed_time

        # Example of updating the valve mode after 10 minutes
        if elapsed_time > 600:
            with flow_lock:
                shared_data["valve_mode"] = "clean_flow"

        time.sleep(1)

from flask import Flask, request, render_template, send_file, jsonify, Response
import pandas as pd
import os
from multiprocessing import Pool, Lock
from io import StringIO
import time  # Import time for runtime measurement



# --------------------------------------------------------
# Flask app setup
app = Flask(__name__)
# The upload .csv it will be on 'uploads' folder 
UPLOAD_FOLDER = 'uploads'
# The sorted .csv it will be on 'results' folder
RESULT_FOLDER = 'results'

# The function os.makedirs() is used to create directories (folders) in the file system. It can also create intermediate directories if they don't exist.

os.makedirs(UPLOAD_FOLDER, exist_ok=True) # If UPLOAD_FOLDER = 'uploads', this creates a directory named uploads in the current working directory.

os.makedirs(RESULT_FOLDER, exist_ok=True) # If RESULT_FOLDER = 'result', this creates a directory named result in the current working directory.



# -------------------------------------------------


""" 
varibles:
* log_stream:
- A StringIO object acts as an in-memory file-like object.
- It is used to store log messages that can be retrieved and displayed later (for ex : in a web interface of ours).
Logs written to this object can be accessed programmatically.

* process_count:

A global variable to track the number of threads or processes being used.
For example, if you're using multiprocessing or multithreading, this counter will help you know how many threads/processes are running concurrently.
process_count_lock:

A thread-safe lock to ensure that updates to process_count are safe when multiple threads or processes are running.
Without this lock, two threads could update process_count at the same time, leading to incorrect values (a "race condition").




"""
# --------------------------------
# Logging setup
log_stream = StringIO() # A StringIO object acts as an in-memory file-like object.

# Thread counter and lock
process_count = 0  # Tracks total processes used
process_count_lock = Lock()

def log(message):
    """Log a message to both console and StringIO.
    example means???

    Thread 0 started. Total threads: 1
    Thread 1 started. Total threads: 2
    ect .........

    """
    global log_stream
    log_message = f"{message}\n"
    print(log_message, end="")  # Print to console for debugging
    log_stream.write(log_message)
    log_stream.seek(0)


# ----------------------------------------

"""

Base Case:

If the data list has 1 or fewer elements, it is already sorted, so the function returns it.
Recursive Case:

Split the data list into two halves:
left: First half of the list (from the beginning to the midpoint).
right: Second half of the list (from the midpoint to the end).
Recursively call merge_sort on both halves to sort them.
Merge the Sorted Halves:

Use a separate merge function to combine the two sorted halves (left and right) into one sorted list.

"""

# Merge function
def merge(left, right):
    """Merge two sorted arrays."""
    result = []
    i = j = 0
# left --> p
# right --> q

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


# Recursive Merge Sort function (no multiprocessing in recursive calls)
def merge_sort(data):
    """Perform regular merge sort (no multiprocessing)."""
    if len(data) <= 1:
        return data
# mid is the half of eq
    mid = len(data) // 2
# p before with mid on left hand side
    left = merge_sort(data[:mid])
# q after mid on right hand side
    right = merge_sort(data[mid:])

    return merge(left, right)

#----------------------------------


"""Explanation:
This is an optimized version of merge sort that uses parallel processing to split the sorting work into multiple threads or processes. Here's how it works:
"""
# Parallel Merge Sort at the Top Level
def parallel_merge_sort(data):
    """Perform parallel merge sort using multiprocessing with 2 threads."""
    if len(data) <= 1: # If the list has 1 or fewer elements, it’s already sorted, and the function returns it.
        return data
# Split the input list data into two halves
    mid = len(data) // 2
    left, right = data[:mid], data[mid:]

# Track and Log Process Count:
    global process_count, process_count_lock
    with process_count_lock:
        process_count += 2  # Increment process count (one for left, one for right)

    log(f"[THREADS] Starting two processes for sorting: left ({len(left)} items), right ({len(right)} items)")

    # Use 2 processes in the multiprocessing pool
    with Pool(processes=2) as pool:
        left_sorted, right_sorted = pool.map(merge_sort, [left, right])

    return merge(left_sorted, right_sorted)



@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/get_columns', methods=['POST'])
def get_columns():
    """Get column names from the uploaded CSV."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected!"}), 400

    # Save the file temporarily
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Read the first row of the CSV to get column names
    try:
        if os.path.getsize(file_path) == 0:  # Check for empty file
            return jsonify({"error": "Uploaded file is empty!"}), 400
        df = pd.read_csv(file_path, nrows=0)  # Read only the header
        columns = df.columns.tolist()
        return jsonify({"columns": columns})
    except pd.errors.EmptyDataError:
        return jsonify({"error": "The file is empty or not a valid CSV!"}), 400
    except Exception as e:
        log(f"Error in /get_columns: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route('/upload', methods=['POST'])
def upload_file():
    """Sort the selected column in the uploaded CSV."""
    global log_stream, process_count
    log_stream = StringIO()  # Reset log stream for new request
    process_count = 0  # Reset process count

    # Get file name from the hidden input
    file_name = request.form.get('file-name')
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return "File not found! Please try uploading again.", 400

    # Read the uploaded CSV file
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return f"Error reading file: {str(e)}", 400

    # Get the selected column for sorting
    selected_column = request.form.get('column')
    sorting_order = request.form.get('order', 'ascending')  # Default to ascending if not provided

    # Validate the selected column
    if selected_column not in df.columns:
        return f"Selected column '{selected_column}' does not exist!", 400
    if not pd.api.types.is_numeric_dtype(df[selected_column]):
        return f"Selected column '{selected_column}' is not numeric!", 400

    # Perform merge sort with and without threads
    unsorted_data = df[selected_column].tolist()

    # Without threads
    start_time_no_threads = time.time()
    sorted_without_threads = merge_sort(unsorted_data)
    no_thread_runtime = time.time() - start_time_no_threads

    # With threads
    start_time_threads = time.time()
    sorted_with_threads = parallel_merge_sort(unsorted_data)
    thread_runtime = time.time() - start_time_threads

    # Adjust sorting order (if descending)
    if sorting_order == 'descending':
        sorted_without_threads.reverse()
        sorted_with_threads.reverse()

    # Log both runtimes in a single sentence
    log(f"Sorting completed: Without threads = {no_thread_runtime:.6f} seconds, With threads = {thread_runtime:.6f} seconds, Total processes used = {process_count}")

    # Save the sorted data (use the one sorted with threads)
    df[selected_column] = sorted_with_threads
    result_path = os.path.join(RESULT_FOLDER, 'sorted_' + file_name)
    df.to_csv(result_path, index=False)

    return send_file(result_path, as_attachment=True)


@app.route('/logs', methods=['GET'])
def get_logs():
    """Return activity logs."""
    global log_stream
    log_stream.seek(0)
    logs = log_stream.read()
    return Response(logs, mimetype='text/plain')

# Ensure multiprocessing works correctly
if __name__ == '__main__':
    app.run(debug=True)

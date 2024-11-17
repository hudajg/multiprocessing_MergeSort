from flask import Flask, request, render_template, send_file, jsonify, Response
import pandas as pd
import os
from multiprocessing import Pool, Lock
from io import StringIO
import time  # Import time for runtime measurement

# Flask app setup
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Logging setup
log_stream = StringIO()

# Thread counter and lock
process_count = 0  # Tracks total processes used
process_count_lock = Lock()

def log(message):
    """Log a message to both console and StringIO."""
    global log_stream
    log_message = f"{message}\n"
    print(log_message, end="")  # Print to console for debugging
    log_stream.write(log_message)
    log_stream.seek(0)

# Merge function
def merge(left, right):
    """Merge two sorted arrays."""
    result = []
    i = j = 0

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

    mid = len(data) // 2
    left = merge_sort(data[:mid])
    right = merge_sort(data[mid:])

    return merge(left, right)

# Parallel Merge Sort at the Top Level
def parallel_merge_sort(data):
    """Perform parallel merge sort using multiprocessing with 4 threads."""
    if len(data) <= 1:
        return data

    mid = len(data) // 2
    left, right = data[:mid], data[mid:]

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

# Parallel Merge Sort 
## Objective:
This project demonstrates the implementation of the **Merge Sort algorithm** with parallel processing using Python's `multiprocessing` library. The objective is to compare the performance of **sequential merge sort** and **parallel merge sort** on both small and large datasets. 

The project highlights:
- The efficiency of parallel processing for sorting large datasets.
- The impact of threading overhead on smaller datasets.
- A user-friendly web interface built using Flask for uploading CSV files, selecting columns, and downloading sorted results.

## Features:
- **Sequential and Parallel Merge Sort:** Implements both versions of the algorithm to analyze and compare their performance.
- **Dynamic Benchmarking:** Measures runtime for both approaches and logs the results for analysis.
- **Web Application:** Provides a clean interface for uploading datasets, selecting numeric columns for sorting, and downloading the results.
- **Dataset Handling:** 
  - Uses a **synthetic dataset** with 1 million rows and 10 million for benchmarking large datasets.
  - Includes support for **small datasets** sourced from Kaggle.
- **Error Handling:** Handles invalid, empty, or non-numeric column selections gracefully.

## Technologies Used:
- **Python**:
  - `Flask`: Web framework, was used to build the user interface, handle routing, and store data in local files instead of using a database.
  - `Multiprocessing`: Library for implementing parallelism in the merge sort algorithm.
  - `Pandas`: Library for handling CSV files and data manipulation.
  - **Java script** : Used for enhancing the interactivity of the web interface.
- **HTML/CSS**: Front-end for the user interface.

## How it Works:
1. **Upload CSV File**: Users upload a CSV file through the web interface.
2. **Select a Column**: The application dynamically detects numeric columns for sorting.
3. **Perform Sorting**:
   - **Without Threads**: Executes a sequential merge sort and logs the runtime.
   - **With Threads**: Executes a parallel merge sort using multiprocessing and logs the runtime.
4. **Download Results**: Users can download the sorted file.
5. **Logs**: View detailed activity logs, including runtimes and the number of processes used.

## Performance Insights:
- **Small Datasets**: Sequential merge sort performs better due to low overhead.
- **Large Datasets**: Parallel merge sort excels by leveraging multi-core processing power.
- Logs clearly show the trade-offs between both approaches.

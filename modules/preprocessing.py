"""Preprocessing module for task data transformations.

Functions:
  preprocess_task_data(tasks):
    Preprocesses the tasks data for EDA and analytics.

  _remove_outlier_tasks(tasks):
    Removes outliers in tasks.
    
  _convert_ms_to_s(ms):
    Converts a "minutes:seconds" string to total seconds as an integer.

  _convert_to_dt_cols(df, columns):
    Converts string time columns to useable datetime columns.
"""

import numpy as np
import pandas as pd

def preprocess_task_data(tasks):
  """Preprocesses the tasks data for EDA and analytics.

  The pre-processing procedure is as follows:
    1. NaN values are removed
    2. Columns are renamed for simplicity and ease of access
    3. Depreciated task type names are removed, example "Part Return"
    4. Strings with dates are converted to datetime formats
    5. Creation Date and Queue Time columns are created
  
  Args:
    tasks: pandas dataframe with each row containing a 
           single task.
  
  Returns:
    tasks: pandas dataframe that has been preprocessed with 
           each row containing a single task.
  """

  # Drop all NaN values
  tasks = tasks.dropna().reset_index(drop=True)

  # Rename Columns
  new_col_names = {'Duration (m:s)': 'Duration',
                   'Task #': 'Task No',
                   'Name': 'Task Type',
                   'Workcenter': 'Work Center'}
  tasks = tasks.rename(columns=new_col_names, errors='raise')

  # Remove Part Return Tasks 
  tasks = tasks[tasks['Task Type'] != 'Part Return']

  # Duration given as a string "minutes:seconds", need to convert to seconds
  tasks['Duration'] = tasks['Duration'].apply(_convert_ms_to_s)

  # Change Creation Time, Start Time, and End Time columns to datetime columns
  col_times = ['Creation Time', 'Start Time', 'End Time']
  tasks = _convert_to_dt_cols(tasks, col_times)

  # Add Creation Date and Queue Time columns
  creation_date = tasks['Creation Time'].dt.floor('d')
  queue_time = ((tasks['Start Time'] - tasks['Creation Time'])
                  .dt.total_seconds()
                  .astype('int64'))
  tasks.insert(7, 'Creation Date', creation_date)
  tasks.insert(11, 'Queue Time', queue_time)

  tasks = _remove_outlier_tasks(tasks)
  return tasks

def _remove_outlier_tasks(tasks):
  """Removes outliers in tasks."""
  tasks = tasks[(tasks['Duration'] >= 10) & (tasks['Duration'] <= 3600)]
  tasks = tasks[(tasks['Distance'] >= 10) & (tasks['Distance'] <= 3600)]
  tasks = tasks[tasks['Queue Time'] <= 4500]
  return tasks

def _convert_ms_to_s(ms):
  """Converts a "minutes:seconds" string to total seconds as an integer."""
  if ms is not np.nan:
    temp = ms.split(':')
    min = int(temp[0])
    sec = int(temp[1].split('.')[0])
    total_secs = min * 60 + sec
  else:
    total_secs = np.nan
  return total_secs

def _convert_to_dt_cols(df, columns):
  """Converts string time columns to useable datetime columns."""
  for col in columns:
    df[col] = pd.to_datetime(df[col])
  return df